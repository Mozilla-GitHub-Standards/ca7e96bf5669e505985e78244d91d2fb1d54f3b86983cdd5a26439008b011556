# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
""" BSO object -- used for (de)serialization
"""

import re

_FIELDS = set(('id', 'collection', 'sortindex', 'modified',
               'payload', 'payload_size', 'ttl'))

MAX_TTL = 31536000
MAX_ID_SIZE = 64
MAX_PAYLOAD_SIZE = 256 * 1024
MAX_SORTINDEX_VALUE = 999999999
MIN_SORTINDEX_VALUE = -999999999
VALID_ID_REGEX = re.compile("^[a-zA-Z0-9._-]+$")


class BSO(dict):
    """Holds BSO info"""

    def __init__(self, data=None, converters=None):
        if data is None:
            data = {}
        if converters is None:
            converters = {}

        try:
            data_items = data.items()
        except AttributeError:
            msg = "BSO data must be dict-like, not %s"
            raise ValueError(msg % (type(data),))

        for name, value in data_items:
            if value is not None:
                if not isinstance(value, (int, long, float, basestring)):
                    msg = "BSO fields must be scalar values, not %s"
                    raise ValueError(msg % (type(value),))
            if name not in _FIELDS:
                raise ValueError("Unknown BSO field %r" % (name,))
            if name in converters:
                value = converters[name](value)
            if value is None:
                continue

            self[name] = value

    def validate(self):
        """Validates the values the BSO has."""

        # Check that id field is well-formed.
        if 'id' in self:
            value = self['id']
            # Check that it's base64url-compliant.
            # Doing the regex match first has the nice side-effect of
            # erroring out if the value is not a string or unicode object.
            # This avoids accidentally coercing other types to a string.
            try:
                if not VALID_ID_REGEX.match(value):
                    return False, 'invalid id'
            except TypeError:
                return False, 'invalid id'
            # Make sure it's stored as a bytestring, not a unicode object.
            # This won't fail because we've checked for valid chars above.
            value = str(self['id'])
            if len(value) > MAX_ID_SIZE:
                return False, 'invalid id'
            self['id'] = value

        # Check that the ttl is an int, and less than one year.
        if 'ttl' in self:
            try:
                ttl = int(self['ttl'])
            except ValueError:
                return False, 'invalid ttl'
            if ttl < 0 or ttl > MAX_TTL:
                return False, 'invalid ttl'
            self['ttl'] = ttl

        # Check that the sortindex is a valid integer.
        # Convert from other types as necessary.
        if 'sortindex' in self:
            try:
                self['sortindex'] = int(self['sortindex'])
            except ValueError:
                return False, 'invalid sortindex'
            if self['sortindex'] > MAX_SORTINDEX_VALUE:
                return False, 'invalid sortindex'
            if self['sortindex'] < MIN_SORTINDEX_VALUE:
                return False, 'invalid sortindex'

        # Check that the payload is a string, and is not too big.
        payload = self.get('payload')
        if payload is not None:
            if not isinstance(payload, basestring):
                return False, 'payload not a string'
            if len(payload.encode("utf8")) > MAX_PAYLOAD_SIZE:
                return False, 'payload too large'

        return True, None