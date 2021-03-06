"""
The controller is the interface for all remote method calls over dbus.
The Controller class creates the controller,
which can be used to invoke the remote methods.
"""

from __future__ import absolute_import, print_function, unicode_literals

import ast
from .connection import Connection
from .exception import ConnectionReturnError

__all__ = ["Controller", ]


class Controller(object):

    """A Class to control all interactions with the gst-switch-srv over dbus.
    Provides the interface for higher level interactions

    :param: None
    """
    COMPOSITE_NONE = 0
    COMPOSITE_PIP = 1
    COMPOSITE_DUAL_PREVIEW = 2
    COMPOSITE_DUAL_EQUAL = 3
    VIDEO_CHANNEL_A = ord('A')
    VIDEO_CHANNEL_B = ord('B')
    AUDIO_CHANNEL = ord('a')

    def __init__(
            self,
            address="tcp:host=127.0.0.1,port=5000",
            bus_name='us.timvideos.gstswitch.SwitchController',
            object_path="/us/timvideos/gstswitch/SwitchController",
            default_interface=(
                "us.timvideos.gstswitch.SwitchControllerInterface")
    ):

        super(Controller, self).__init__()

        self._address = None
        self._bus_name = None
        self._object_path = None
        self._default_interface = None
        self.connection = None

        self.address = address
        self.bus_name = bus_name
        self.object_path = object_path
        self.default_interface = default_interface

        self.callbacks_preview_port_added = []
        self.callbacks_preview_port_removed = []
        self.callbacks_new_mode_online = []
        self.callbacks_show_face_marker = []
        self.callbacks_show_track_marker = []
        self.callbacks_select_face = []

    @property
    def address(self):
        """
        Get the address
        """
        return self._address

    @address.setter
    def address(self, address):
        """Set the Address
        http://dbus.freedesktop.org/doc/dbus-specification.html#addresses
        """
        if not address:
            raise ValueError("Address '{0}' cannot be blank")
        else:
            adr = str(address)
            if adr.find(':') > 0:
                self._address = adr
            else:
                raise ValueError("Address must follow specifications mentioned"
                                 " at http://dbus.freedesktop.org/doc/"
                                 "dbus-specification.html#addresses")

    @property
    def bus_name(self):
        """Get the bus name
        """
        if self._bus_name is None:
            return None
        return self._bus_name

    @bus_name.setter
    def bus_name(self, bus_name):
        """Set the Bus Name
        http://dbus.freedesktop.org/doc/dbus-specification.html\
        #message-protocol-names-bus
        """
        if bus_name is None:
            self._bus_name = None
            return
        bus = str(bus_name)
        self._bus_name = bus

    @property
    def object_path(self):
        """Get the object path
        """
        return self._object_path

    @object_path.setter
    def object_path(self, object_path):
        """Set the object_path
        http://dbus.freedesktop.org/doc/dbus-specification.html\
        #message-protocol-marshaling-object-path
        """
        if not object_path:
            raise ValueError("object_path '{0} cannot be blank'")
        else:
            obj = str(object_path)
            if obj[0] == '/':
                self._object_path = obj
            else:
                raise ValueError("object_path must follow specifications"
                                 " mentioned at "
                                 "http://dbus.freedesktop.org/doc/"
                                 "dbus-specification.html"
                                 "#message-protocol-marshaling-object-path""")

    @property
    def default_interface(self):
        """Get the default interface
        """
        return self._default_interface

    @default_interface.setter
    def default_interface(self, default_interface):
        """Set the default_interface
        http://dbus.freedesktop.org/doc/dbus-specification.html\
        #message-protocol-names-interface
        """
        if not default_interface:
            raise ValueError("default_interface '{0} cannot be blank'")
        else:
            intr = str(default_interface)
            if intr.count('.') > 1:
                self._default_interface = intr
            else:
                raise ValueError("default_interface must follow "
                                 "specifications mentioned at "
                                 "http://dbus.freedesktop.org/"
                                 "doc/dbus-specification.html"
                                 "#message-protocol-names-interface")

    def establish_connection(self):
        """Establishes a fresh connection to the dbus
        Connection stored as self.connection

        :param: None
        :returns: None
        """
        self.connection = Connection(
            address=self.address,
            bus_name=self.bus_name,
            object_path=self.object_path,
            default_interface=self.default_interface)

        self.connection.connect_dbus()
        self.connection.signal_subscribe(self.cb_signal_handler)

    def cb_signal_handler(self, connection, sender_name, object_path,
                          interface_name, signal_name, parameters, user_data):
        """Private Callback passed into Gio's signal_subscribe and called
        for every signal arriving on the bus.

        For params see Gio-Docs: <https://lazka.github.io/pgi-docs/#Gio-2.0/
        classes/DBusConnection.html#Gio.DBusConnection.signal_subscribe>
        """
        try:
            callbacks = getattr(self, 'callbacks_'+signal_name)
            if not isinstance(callbacks, list):
                raise AttributeError()

            unpack = parameters.unpack()
            for callback in callbacks:
                # We're passing the values unpacked from the GVariant as-is
                # to the callback. The auther of the callback is responsible
                # to make sure that it's arguments match with the DBus Signal
                # Specification for the particular Signal he's subscribing for
                # Disable pylint-warning because we know what we're doing here.

                # pylint: disable=star-args
                callback(*unpack)

        except AttributeError:
            pass

    def get_compose_port(self):
        """Get the compose port number

        :param: None
        :returns: compose port number
        """
        conn = self.connection.get_compose_port()
        try:
            compose_port = conn.unpack()[0]
            return compose_port
        except AttributeError:
            raise ConnectionReturnError('Connection returned invalid values.'
                                        'Should return a GVariant tuple')

    def get_encode_port(self):
        """Get the encode port number

        :param: None
        :returns: encode port number
        """
        conn = self.connection.get_encode_port()
        try:
            encode_port = conn.unpack()[0]
            return encode_port
        except AttributeError:
            raise ConnectionReturnError('Connection returned invalid values.'
                                        ' Should return a GVariant tuple')

    def get_audio_port(self):
        """Get the audio port number

        :param: None
        :returns: audio port number
        """
        conn = self.connection.get_audio_port()
        try:
            audio_port = conn.unpack()[0]
            return audio_port
        except AttributeError:
            raise ConnectionReturnError('Connection returned invalid values. '
                                        'Should return a GVariant tuple')

    def get_preview_ports(self):
        """Get all the preview ports

        :param: None
        :returns: list of all preview ports
        """
        conn = self.connection.get_preview_ports()
        try:
            res = conn.unpack()[0]
            preview_ports = self.parse_preview_ports(res)
            return preview_ports
        except AttributeError:
            raise ConnectionReturnError('Connection returned invalid values. '
                                        'Should return a GVariant tuple')

    def set_composite_mode(self, mode):
        """Set the current composite mode.
        Modes allowed are:
         - COMPOSITE_NONE
         - COMPOSITE_PIP
         - COMPOSITE_DUAL_PREVIEW
         - COMPOSITE_DUAL_EQUAL

        :param mode: new composite mode
        :returns: True when requested
        """
        self.establish_connection()
        # only modes from 0 to 3 are supported
        res = None
        if mode in range(0, 4):
            try:
                conn = self.connection.set_composite_mode(mode)
                res = conn.unpack()[0]
            except AttributeError:
                raise ConnectionReturnError('Connection returned invalid '
                                            'values. Should return a '
                                            'GVariant tuple')
        else:
            pass
            # raise some Exception
        return res

    def get_composite_mode(self):
        """Set the current composite mode.
        Modes allowed are:
         - COMPOSITE_NONE
         - COMPOSITE_PIP
         - COMPOSITE_DUAL_PREVIEW
         - COMPOSITE_DUAL_EQUAL

        :returns: The current composition mode
        """
        self.establish_connection()
        # only modes from 0 to 3 are supported
        res = None
        try:
            conn = self.connection.get_composite_mode()
            res = conn.unpack()[0]
            if res in range(0, 4):
                print("Current composite mode is %u" % (res))
        except AttributeError:
            raise ConnectionReturnError('Connection returned invalid '
                                        'values. Should return a '
                                        'GVariant tuple')
        return res

    def set_encode_mode(self, channel):
        """Set the encode mode
        WARNING: THIS DOES NOT WORK.

        :param: channel
        :returns: True when requested
        """
        self.establish_connection()
        try:
            conn = self.connection.set_encode_mode(channel)
            res = conn.unpack()[0]
            if res is not True:
                # raise some exception
                pass
            return res
        except AttributeError:
            raise ConnectionReturnError('Connection returned invalid values. '
                                        'Should return a GVariant tuple')

    def new_record(self):
        """Start a new recording

        :param: None
        """
        self.establish_connection()
        try:
            conn = self.connection.new_record()
            res = conn.unpack()[0]
            if res is not True:
                # raise some exception
                pass
        except AttributeError:
            raise ConnectionReturnError('Connection returned invalid values. '
                                        'Should return a GVariant tuple')
        return res

    def adjust_pip(self, xpos, ypos, width, height):
        """Change the PIP position and size

        :param xpos: the x position of the PIP
        :param ypos: the y position of the PIP
        :param width: the width of the PIP
        :param height: the height of the PIP
        :returns: result - PIP has been changed succefully
        """
        self.establish_connection()
        try:
            conn = self.connection.adjust_pip(xpos, ypos, width, height)
            res = conn.unpack()[0]
        except AttributeError:
            raise ConnectionReturnError('Connection returned invalid values. '
                                        'Should return a GVariant tuple')
        # to-do - parse
        return res

    def switch(self, channel, port):
        """Switch the channel to the target port

        :param channel: The channel to be switched:
            VIDEO_CHANNEL_A
            VIDEO_CHANNEL_B
            AUDIO_CHANNEL
        :param port: The target port number
        :returns: True when requested
        """
        self.establish_connection()
        try:
            conn = self.connection.switch(channel, port)
            res = conn.unpack()[0]
            if res is not True:
                # raise some exception
                pass
            return res
        except AttributeError:
            raise ConnectionReturnError('Connection returned invalid values. '
                                        'Should return a GVariant tuple')

    def click_video(self, xpos, ypos, width, height):
        """User click on the video

        :param xpos:
        :param ypos:
        :param width:
        :param height:
        :returns: True when requested
        """
        self.establish_connection()
        try:
            conn = self.connection.click_video(xpos, ypos, width, height)
            res = conn.unpack()[0]
            if res is not True:
                # raise some exception
                pass
        except:
            raise ConnectionReturnError('Connection returned invalid values. '
                                        'Should return a GVariant tuple')
        return res

    def mark_face(self, faces):
        """Mark faces

        :param faces: tuple having four elements
        :returns: True when requested
        """
        # faces is list of a tuple of four elements
        self.establish_connection()
        self.connection.mark_face(faces)

    def mark_tracking(self, faces):
        """Mark tracking

        :param faces: tuple having four elements
        :returns: True when requested
        """
        self.establish_connection()
        self.connection.mark_tracking(faces)

    @classmethod
    def parse_preview_ports(cls, res):
        """Parses the preview_ports string"""
        # res = '[(a, b, c), (a, b, c)*]'
        try:
            liststr = ast.literal_eval(res)
        except (ValueError, SyntaxError):
            raise ConnectionReturnError(("Connection returned "
                                         "invalid values:{0}")
                                        .format(res))
        preview_ports = []
        for tupl in liststr:
            preview_ports.append(int(tupl[0]))
        return preview_ports

    def on_preview_port_added(self, callback):
        """Register a Callback for the preview_port_added Signal
        which is fired, when a new Video or Audio-Source is connected
        to the Server and the Server opens a new Port where the Signal
        of this Source can be previewed.

        The Callback takes the following Arguments:
           int port  - The TCP-Port on the Server where the
                       Preview-Stream can be obtained from
           int serve - Type of Material served
                       0 = GST_SERVE_NOTHING
                       1 = GST_SERVE_VIDEO_STREAM
                       2 = GST_SERVE_VIDEO_AUDIO
           int type  - Type of Branch serving the Video
        """

        if not callable(callback):
            raise ValueError('Provided argument callback is not callable')

        self.callbacks_preview_port_added.append(callback)

    def on_preview_port_removed(self, callback):
        """Register a Callback for the preview_port_removed Signal
        which is fired, when a Video or Audio-Source is disconnected
        from the Server and the Server closes its Port where the Signal
        of this Source was provided.

        The Callback takes the following Arguments:
            int port  - The TCP-Port on the Server where the
                        Preview-Stream was provided
            int serve - Type of Material served
                        0 = GST_SERVE_NOTHING
                        1 = GST_SERVE_VIDEO_STREAM
                        2 = GST_SERVE_VIDEO_AUDIO
            int type  - Type of Branch serving the Video
        """

        if not callable(callback):
            raise ValueError('Provided argument callback is not callable')

        self.callbacks_preview_port_removed.append(callback)

    def on_new_mode_online(self, callback):
        """Register a Callback for the new_mode_online Signal
        which is fired, when the Composition-Mode was changed successfully.

        The Callback takes the following Argument:
            int mode  - The new Mode
                        0 = COMPOSE_MODE_NONE
                        1 = COMPOSE_MODE_PIP
                        2 = COMPOSE_MODE_DUAL_PREVIEW
                        3 = COMPOSE_MODE_DUAL_EQUAL
        """

        if not callable(callback):
            raise ValueError('Provided argument callback is not callable')

        self.callbacks_new_mode_online.append(callback)

    def on_show_face_marker(self, callback):
        """Register a Callback for the show_face_marker Signal
        which is fired, when a Client has successfully set a face-marker
        by calling mark_face.

        The Callback takes the following Argument:
            array faces  - An Array of Tuples of 4 ints, each specifying
                           x, y, w, and h of a tracked region
        """

        if not callable(callback):
            raise ValueError('Provided argument callback is not callable')

        self.callbacks_show_face_marker.append(callback)

    def on_show_track_marker(self, callback):
        """Register a Callback for the show_track_marker Signal
        which is fired, when a Client has successfully set a track-marker
        by calling mark_tracking.

        The Callback takes the following Argument:
            array faces  - An Array of Tuples of 4 ints, each specifying
                           x, y, w, and h of a tracked region
        """

        if not callable(callback):
            raise ValueError('Provided argument callback is not callable')

        self.callbacks_show_track_marker.append(callback)

    def on_select_face(self, callback):
        """Register a Callback for the select_face Signal
        which is fired, when a Client has successfully selected a face
        by calling click_video.

        The Callback takes the following Argument:
            int x  - X-Coordinate of the Click
            int y  - Y-Coordinate of the Click
        """

        if not callable(callback):
            raise ValueError('Provided argument callback is not callable')

        self.callbacks_select_face.append(callback)
