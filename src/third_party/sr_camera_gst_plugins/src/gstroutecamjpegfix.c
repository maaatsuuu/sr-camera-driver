#include <gst/gst.h>
#include <gst/rtp/gstrtpbuffer.h>

#include <stdio.h>

#define GST_TYPE_ROUTE_CAM_JPEG_FIX (gst_route_cam_jpeg_fix_get_type())
#define GST_ROUTE_CAM_JPEG_FIX(obj) ((GstRouteCamJpegFix *) (obj))

typedef struct _GstRouteCamJpegFix GstRouteCamJpegFix;
typedef struct _GstRouteCamJpegFixClass GstRouteCamJpegFixClass;

struct _GstRouteCamJpegFix
{
  GstElement parent;
  GstPad *sinkpad;
  GstPad *srcpad;
  gboolean fix_enabled;
  gint media_width;
  gint media_height;
  guint64 fixed_buffers;
};

struct _GstRouteCamJpegFixClass
{
  GstElementClass parent_class;
};

G_DEFINE_TYPE (GstRouteCamJpegFix, gst_route_cam_jpeg_fix, GST_TYPE_ELEMENT)

GST_DEBUG_CATEGORY_STATIC (route_cam_jpeg_fix_debug);
#define GST_CAT_DEFAULT route_cam_jpeg_fix_debug

static GstStaticPadTemplate sink_template = GST_STATIC_PAD_TEMPLATE (
    "sink",
    GST_PAD_SINK,
    GST_PAD_ALWAYS,
    GST_STATIC_CAPS (
        "application/x-rtp, "
        "media = (string) video, "
        "clock-rate = (int) 90000, "
        "encoding-name = (string) JPEG; "
        "application/x-rtp, "
        "media = (string) video, "
        "payload = (int) 26, "
        "clock-rate = (int) 90000"));

static GstStaticPadTemplate src_template = GST_STATIC_PAD_TEMPLATE (
    "src",
    GST_PAD_SRC,
    GST_PAD_ALWAYS,
    GST_STATIC_CAPS (
        "application/x-rtp, "
        "media = (string) video, "
        "clock-rate = (int) 90000, "
        "encoding-name = (string) JPEG; "
        "application/x-rtp, "
        "media = (string) video, "
        "payload = (int) 26, "
        "clock-rate = (int) 90000"));

static void
gst_route_cam_jpeg_fix_update_caps (GstRouteCamJpegFix *self, GstCaps *caps)
{
  const GstStructure *structure;
  const gchar *dimensions;
  gint width = 0;
  gint height = 0;

  self->fix_enabled = FALSE;
  self->media_width = 0;
  self->media_height = 0;

  if (!caps || gst_caps_is_empty (caps)) {
    return;
  }

  structure = gst_caps_get_structure (caps, 0);
  dimensions = gst_structure_get_string (structure, "x-dimensions");
  if (!dimensions || sscanf (dimensions, "%d,%d", &width, &height) != 2) {
    GST_INFO_OBJECT (self, "x-dimensions is not set");
    return;
  }

  self->media_width = width;
  self->media_height = height;
  self->fix_enabled = width > 2040 || height > 2040;

  GST_INFO_OBJECT (
      self,
      "x-dimensions=%dx%d, fix_enabled=%s",
      width,
      height,
      self->fix_enabled ? "true" : "false");
}

static gboolean
gst_route_cam_jpeg_fix_sink_event (GstPad *pad, GstObject *parent, GstEvent *event)
{
  GstRouteCamJpegFix *self = GST_ROUTE_CAM_JPEG_FIX (parent);

  (void) pad;

  if (GST_EVENT_TYPE (event) == GST_EVENT_CAPS) {
    GstCaps *caps = NULL;
    gst_event_parse_caps (event, &caps);
    gst_route_cam_jpeg_fix_update_caps (self, caps);
  }

  return gst_pad_push_event (self->srcpad, event);
}

static GstFlowReturn
gst_route_cam_jpeg_fix_chain (GstPad *pad, GstObject *parent, GstBuffer *buffer)
{
  GstRouteCamJpegFix *self = GST_ROUTE_CAM_JPEG_FIX (parent);
  GstRTPBuffer rtp = GST_RTP_BUFFER_INIT;
  guint8 *payload;
  guint payload_len;

  (void) pad;

  if (!self->fix_enabled) {
    return gst_pad_push (self->srcpad, buffer);
  }

  buffer = gst_buffer_make_writable (buffer);
  if (!gst_rtp_buffer_map (buffer, GST_MAP_READWRITE, &rtp)) {
    GST_WARNING_OBJECT (self, "failed to map RTP buffer");
    return gst_pad_push (self->srcpad, buffer);
  }

  payload = gst_rtp_buffer_get_payload (&rtp);
  payload_len = gst_rtp_buffer_get_payload_len (&rtp);

  if (payload_len >= 8 && (payload[6] != 0 || payload[7] != 0)) {
    GST_LOG_OBJECT (
        self,
        "override RTP/JPEG dimension bytes %u x %u for %dx%d",
        payload[6],
        payload[7],
        self->media_width,
        self->media_height);
    payload[6] = 0;
    payload[7] = 0;
    self->fixed_buffers++;
  }

  gst_rtp_buffer_unmap (&rtp);
  return gst_pad_push (self->srcpad, buffer);
}

static void
gst_route_cam_jpeg_fix_init (GstRouteCamJpegFix *self)
{
  self->sinkpad = gst_pad_new_from_static_template (&sink_template, "sink");
  gst_pad_set_event_function (self->sinkpad, GST_DEBUG_FUNCPTR (gst_route_cam_jpeg_fix_sink_event));
  gst_pad_set_chain_function (self->sinkpad, GST_DEBUG_FUNCPTR (gst_route_cam_jpeg_fix_chain));
  gst_element_add_pad (GST_ELEMENT (self), self->sinkpad);

  self->srcpad = gst_pad_new_from_static_template (&src_template, "src");
  gst_element_add_pad (GST_ELEMENT (self), self->srcpad);

  self->fix_enabled = FALSE;
  self->media_width = 0;
  self->media_height = 0;
  self->fixed_buffers = 0;
}

static void
gst_route_cam_jpeg_fix_class_init (GstRouteCamJpegFixClass *klass)
{
  GstElementClass *element_class = GST_ELEMENT_CLASS (klass);

  gst_element_class_add_static_pad_template (element_class, &sink_template);
  gst_element_class_add_static_pad_template (element_class, &src_template);
  gst_element_class_set_static_metadata (
      element_class,
      "RouteCAM RTP/JPEG dimension fix",
      "Filter/Network/RTP",
      "Fixes oversized RTP/JPEG dimension bytes using x-dimensions caps",
      "matsudri");

  GST_DEBUG_CATEGORY_INIT (
      route_cam_jpeg_fix_debug,
      "routecamjpegfix",
      0,
      "RouteCAM RTP/JPEG dimension fix");
}

static gboolean
plugin_init (GstPlugin *plugin)
{
  return gst_element_register (
      plugin,
      "routecamjpegfix",
      GST_RANK_NONE,
      GST_TYPE_ROUTE_CAM_JPEG_FIX);
}

GST_PLUGIN_DEFINE (
    GST_VERSION_MAJOR,
    GST_VERSION_MINOR,
    routecamjpegfix,
    "RouteCAM RTP/JPEG dimension fix",
    plugin_init,
    PACKAGE_VERSION,
    "LGPL",
    PACKAGE,
    "https://github.com")
