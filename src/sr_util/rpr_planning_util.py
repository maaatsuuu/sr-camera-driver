#!/usr/bin/env python3

from __future__ import annotations

import rclpy
from nav_msgs.msg import Path
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.task import Future
from shape_msgs.msg import Plane
from std_msgs.msg import Header
from trajectory_msgs.msg import JointTrajectory
from vision_msgs.msg import BoundingBox3D

from rpr_planning_interfaces.action import PlanPaintMotion, PlanPresetMotion
from rpr_planning_interfaces.msg import SpanDefinition
from rpr_planning_interfaces.srv import GenerateMotionWaypoints, GenerateSpanPlan


class RprPlanningUtil:
    """Utility class for RPR waypoint/motion planning interfaces."""

    def __init__(
        self,
        node: Node,
        generate_span_plan_service_name: str = "/generate_span_plan",
        generate_motion_waypoints_service_name: str = "/generate_motion_waypoints",
        plan_paint_motion_action_name: str = "/plan_paint_motion",
        plan_preset_motion_action_name: str = "/plan_preset_motion",
        destroy_node_on_close: bool = False,
    ) -> None:
        self._node = node
        self._destroy_node_on_close = bool(destroy_node_on_close)

        # wait_for_interfaces() とエラーログで同じ名前を使えるように保持する。
        self._generate_span_plan_service_name = generate_span_plan_service_name
        self._generate_motion_waypoints_service_name = generate_motion_waypoints_service_name
        self._plan_paint_motion_action_name = plan_paint_motion_action_name
        self._plan_preset_motion_action_name = plan_preset_motion_action_name

        # create_client(サービス型, サービス名)
        self._generate_span_plan_client = self._node.create_client(
            GenerateSpanPlan,
            self._generate_span_plan_service_name,
        )
        self._generate_motion_waypoints_client = self._node.create_client(
            GenerateMotionWaypoints,
            self._generate_motion_waypoints_service_name,
        )

        # ActionClient(ノード, アクション型, アクション名)
        self._plan_paint_motion_client = ActionClient(
            self._node,
            PlanPaintMotion,
            self._plan_paint_motion_action_name,
        )
        self._plan_preset_motion_client = ActionClient(
            self._node,
            PlanPresetMotion,
            self._plan_preset_motion_action_name,
        )

        self._closed = False

    # ---------- common ----------

    def get_logger(self):
        return self._node.get_logger()

    def wait_for_interfaces(self, timeout_sec: float = 5.0) -> None:
        """サービスやアクションのサーバが利用可能になるまで待つ。"""
        service_clients = [
            (self._generate_span_plan_client, self._generate_span_plan_service_name),
            (self._generate_motion_waypoints_client, self._generate_motion_waypoints_service_name),
        ]
        for client, name in service_clients:
            if not client.wait_for_service(timeout_sec=timeout_sec):
                raise RuntimeError(f"{name} service is not available")

        if not self._plan_paint_motion_client.wait_for_server(timeout_sec=timeout_sec):
            raise RuntimeError(
                f"{self._plan_paint_motion_action_name} action server is not available"
            )

        if not self._plan_preset_motion_client.wait_for_server(timeout_sec=timeout_sec):
            raise RuntimeError(
                f"{self._plan_preset_motion_action_name} action server is not available"
            )

    def close(self) -> None:
        """ノード破棄"""
        if self._closed:
            return
        if self._destroy_node_on_close:
            self._node.destroy_node()
        self._closed = True

    def _wait_future_result(
        self,
        future: Future,
        timeout_sec: float,
        interface_name: str,
    ):
        """通信タイムアウトや呼び出し失敗を共通化するユーティリティ"""
        rclpy.spin_until_future_complete(self._node, future, timeout_sec=timeout_sec)

        if not future.done():
            raise RuntimeError(
                f"{interface_name} timed out after {timeout_sec} seconds"
            )

        try:
            result = future.result()
        except Exception as exc:
            raise RuntimeError(f"{interface_name} call failed: {exc}") from exc

        if result is None:
            raise RuntimeError(f"{interface_name} returned no response")

        return result

    def _wait_action_result(
        self,
        send_future: Future,
        action_name: str,
        timeout_sec: float,
    ):
        """Goal 送信後の受理待ちと result 待ちを共通化する。"""
        goal_handle = self._wait_future_result(
            send_future,
            timeout_sec=timeout_sec,
            interface_name=f"{action_name} send_goal",
        )

        if goal_handle is None or not goal_handle.accepted:
            raise RuntimeError(f"{action_name} goal was rejected")

        result_future = goal_handle.get_result_async()
        action_result = self._wait_future_result(
            result_future,
            timeout_sec=timeout_sec,
            interface_name=f"{action_name} get_result",
        )
        return action_result.result


    # ---------- generate span plan service ----------

    def generate_span_plan(
        self,
        wall_header: Header,
        wall_bbox_world: BoundingBox3D,
        timeout_sec: float = 10.0,
    ) -> tuple[bool, str, list[SpanDefinition]]:
        """
        壁面BBoxから span list を生成する。

        戻り値:
            (success, error_message, span_list)
        """
        req = GenerateSpanPlan.Request()
        req.wall_header = wall_header
        req.wall_bbox_world = wall_bbox_world

        self._node.get_logger().info(
            f"Calling GenerateSpanPlan service with wall_header={wall_header}"
        )

        future = self._generate_span_plan_client.call_async(req)
        res = self._wait_future_result(
            future,
            timeout_sec=timeout_sec,
            interface_name=self._generate_span_plan_service_name,
        )

        if res.success:
            self._node.get_logger().info(
                f"GenerateSpanPlan completed. span_count={len(res.span_list)}"
            )
        else:
            self._node.get_logger().warning(
                f"GenerateSpanPlan failed: {res.error_message}"
            )
        # FIXME: res.span_listは上位が読みやすいようにより分解して返すべきかも
        return bool(res.success), str(res.error_message), list(res.span_list)

    # ---------- generate motion waypoints service ----------

    def generate_motion_waypoints(
        self,
        span_list: list[SpanDefinition],
        span_index: int,
        plane_header: Header,
        wall_plane: Plane,
        timeout_sec: float = 10.0,
    ) -> tuple[bool, str, Path]:
        """ span と壁面平面から 1 span 分の paint motion path を生成"""
        req = GenerateMotionWaypoints.Request()
        req.span_list = list(span_list)
        req.span_index = int(span_index)
        req.plane_header = plane_header
        req.wall_plane = wall_plane

        self._node.get_logger().info(
            f"Calling GenerateMotionWaypoints service with span_index={span_index} "
        )

        future = self._generate_motion_waypoints_client.call_async(req)
        res = self._wait_future_result(
            future,
            timeout_sec=timeout_sec,
            interface_name=self._generate_motion_waypoints_service_name,
        )

        if res.success:
            self._node.get_logger().info(
                "GenerateMotionWaypoints completed. "
                f"pose_count={len(res.paint_motion_path.poses)} points."
            )
        else:
            self._node.get_logger().warning(
                f"GenerateMotionWaypoints failed: {res.error_message}"
            )

        return bool(res.success), str(res.error_message), res.paint_motion_path

    # ---------- common for planning action ----------

    def _log_planning_feedback(self, action_label: str, feedback_msg) -> None:
        """PlanPaintMotion と PlanPresetMotion のフィードバックは同じ形式なので共通化"""
        fb = feedback_msg.feedback
        self._node.get_logger().info(
            f"{action_label} feedback: "
            f"current_stage_index={fb.current_stage_index}, "
            f"current_stage_name={fb.current_stage_name}, "
            f"segment_index={fb.segment_index}"
        )

    # ---------- plan paint motion action ----------

    def _plan_paint_motion_feedback_cb(self, feedback_msg) -> None:
        self._log_planning_feedback(self._plan_paint_motion_action_name, feedback_msg)

    def send_plan_paint_motion_goal_async(
        self,
        paint_motion_path: Path,
        with_feedback_log: bool = True,
    ) -> Future:
        """ PlanPaintMotion の goal を非同期送信する"""
        goal = PlanPaintMotion.Goal()
        goal.paint_motion_path = paint_motion_path

        feedback_cb = (
            self._plan_paint_motion_feedback_cb if with_feedback_log else None
        )
        return self._plan_paint_motion_client.send_goal_async(
            goal,
            feedback_callback=feedback_cb,
        )

    def send_plan_paint_motion_goal(
        self,
        paint_motion_path: Path,
        timeout_sec: float = 120.0,
        with_feedback_log: bool = True,
    ) -> tuple[bool, str, list[JointTrajectory], list[str]]:
        """ PlanPaintMotion を同期実行する """
        send_future = self.send_plan_paint_motion_goal_async(
            paint_motion_path=paint_motion_path,
            with_feedback_log=with_feedback_log,
        )
        result = self._wait_action_result(
            send_future,
            action_name=self._plan_paint_motion_action_name,
            timeout_sec=timeout_sec,
        )

        if result.success:
            self._node.get_logger().info(
                "PlanPaintMotion completed. "
                f"stage_count={len(result.stage_trajectories)} "
                f"stage_names={result.stage_names}",
            )
        else:
            self._node.get_logger().warning(
                f"PlanPaintMotion failed: {result.error_message}"
            )

        return (
            bool(result.success),
            str(result.error_message),
            list(result.stage_trajectories),
            list(result.stage_names),
        )
    
    # ---------- plan preset motion action ----------

    def _plan_preset_motion_feedback_cb(self, feedback_msg) -> None:
        self._log_planning_feedback(self._plan_preset_motion_action_name, feedback_msg)

    def send_plan_preset_motion_goal_async(
        self,
        preset_id: str,
        with_feedback_log: bool = True,
    ) -> Future:
        """PlanPresetMotion の goal を非同期送信する。"""
        goal = PlanPresetMotion.Goal()
        goal.preset_id = str(preset_id)

        feedback_cb = (
            self._plan_preset_motion_feedback_cb if with_feedback_log else None
        )
        return self._plan_preset_motion_client.send_goal_async(
            goal,
            feedback_callback=feedback_cb,
        )

    def _send_plan_preset_motion_goal(
        self,
        preset_id: str,
        timeout_sec: float = 120.0,
        with_feedback_log: bool = True,
    ) -> tuple[bool, str, list[JointTrajectory], list[str]]:
        """PlanPresetMotion を同期実行する。"""
        send_future = self.send_plan_preset_motion_goal_async(
            preset_id=preset_id,
            with_feedback_log=with_feedback_log,
        )
        result = self._wait_action_result(
            send_future,
            action_name=self._plan_preset_motion_action_name,
            timeout_sec=timeout_sec,
        )

        if result.success:
            self._node.get_logger().info(
                "PlanPresetMotion completed. "
                f"stage_count={len(result.stage_trajectories)} "
                f"stage_names={result.stage_names}",
            )
        else:
            self._node.get_logger().warning(
                f"PlanPresetMotion failed: {result.error_message}"
            )

        return (
            bool(result.success),
            str(result.error_message),
            list(result.stage_trajectories),
            list(result.stage_names),
        )

    def send_plan_move_home_preset_motion_goal(
        self,
        timeout_sec: float = 120.0,
        with_feedback_log: bool = True,
    ) -> tuple[bool, str, list[JointTrajectory], list[str]]:
        """PlanPresetMotion の move_home プリセット を実行するユーティリティ。"""
        return self._send_plan_preset_motion_goal(
            preset_id="move_home",
            timeout_sec=timeout_sec,
            with_feedback_log=with_feedback_log,
    )

    def send_plan_move_ready_preset_motion_goal(
        self,
        timeout_sec: float = 120.0,
        with_feedback_log: bool = True,
    ) -> tuple[bool, str, list[JointTrajectory], list[str]]:
        """PlanPresetMotion の move_ready プリセット を実行するユーティリティ。"""
        return self._send_plan_preset_motion_goal(
            preset_id="move_ready",
            timeout_sec=timeout_sec,
            with_feedback_log=with_feedback_log,
    )

    def send_plan_lidar_scan_preset_motion_goal(
        self,
        timeout_sec: float = 120.0,
        with_feedback_log: bool = True,
    ) -> tuple[bool, str, list[JointTrajectory], list[str]]:
        """PlanPresetMotion の lidar_scan プリセット を実行するユーティリティ。"""
        return self._send_plan_preset_motion_goal(
            preset_id="lidar_scan",
            timeout_sec=timeout_sec,
            with_feedback_log=with_feedback_log,
    )

    def send_plan_prepare_paint_preset_motion_goal(
        self,
        timeout_sec: float = 120.0,
        with_feedback_log: bool = True,
    ) -> tuple[bool, str, list[JointTrajectory], list[str]]:
        """PlanPresetMotion の prepare_paint プリセット を実行するユーティリティ。"""
        return self._send_plan_preset_motion_goal(
            preset_id="prepare_paint",
            timeout_sec=timeout_sec,
            with_feedback_log=with_feedback_log,
    )

    def send_plan_front_scan_preset_motion_goal(
        self,
        timeout_sec: float = 120.0,
        with_feedback_log: bool = True,
    ) -> tuple[bool, str, list[JointTrajectory], list[str]]:
        """PlanPresetMotion の start_front_scan プリセット を実行するユーティリティ。"""
        return self._send_plan_preset_motion_goal(
            preset_id="start_front_scan",
            timeout_sec=timeout_sec,
            with_feedback_log=with_feedback_log,
    )

__all__ = ["RprPlanningUtil"]