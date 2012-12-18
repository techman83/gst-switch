#!/bin/bash
cd /store/open/gstreamer/stage

#    --gst-debug-level=5
#    --gst-debug="tcpmixsrc*:5,GST_ELEMENT_*:5,GST_PAD*:5" \

./bin/gst-launch-1.0 -v \
    --gst-debug-no-color \
    --gst-debug="tcpmixsrc:5" \
    \
    tcpmixsrc name=source port=3000 \
    fdsink name=sink fd=2 \
    source. ! sink.
