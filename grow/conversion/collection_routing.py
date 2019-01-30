# -*- coding: utf-8 -*-
"""
Utility for converting Grow sites to enable collection level routing. Instead
of storing things that affect routing directly in the document it is stored
at the level of the collection to prevent the need to read every document to
generate the routing information.

WARNING: This feature is used in the `separate_routing` experiment.

Usage:

    grow convert --type=collection_routing
"""

import collections
import logging
import os
import yaml
from grow.common import yaml_utils


ROUTES_FILENAME = '_routes.yaml'
COLLECTION_META_KEYS = ('$path', '$localization', '$view')


class Error(Exception):
    pass


class RoutesData(object):
    """Store and format the routes information pulled from the documents."""

    def __init__(self):
        self.paths = collections.OrderedDict()

    @property
    def data(self):
        """The yaml contents to write to the file."""
        data = collections.OrderedDict()
        data['version'] = 1
        data['pod_paths'] = self.paths
        return data

    def extract_doc(self, doc):
        """Extract the meta information from the doc to use for the routes."""
        raw_data = doc.format.front_matter.raw_data
        data = collections.OrderedDict()

        tagged_keys = tuple(['{}@'.format(key)
                             for key in COLLECTION_META_KEYS])

        for key, value in raw_data.iteritems():
            if key in COLLECTION_META_KEYS or key.startswith(tagged_keys):
                data[key.lstrip('$')] = value

        self.paths[doc.pod_path] = data

    def write_routes(self, pod, collection):
        """Write the converted routes to the configuration file."""
        routes_file = os.path.join(collection.pod_path, ROUTES_FILENAME)

        print ' └─ Writing: {}'.format(routes_file)
        print ''
        output = yaml.dump(
            self.data, Dumper=yaml_utils.PlainTextYamlDumper,
            default_flow_style=False, allow_unicode=True, width=800)
        pod.write_file(routes_file, output)


class ConversionCollection(object):
    """Temporary collection class for doing a conversion for a collection."""

    def __init__(self, pod, collection):
        self.pod = pod
        self.collection = collection
        self.routes_data = RoutesData()

    def convert(self):
        """Perform the conversion to use collection based routing."""
        print 'Converting: {}'.format(self.collection.pod_path)

        # Pull out the meta information from all the docs.
        for doc in self.collection.list_docs_unread():
            self.routes_data.extract_doc(doc)

        self.routes_data.write_routes(self.pod, self.collection)


class Converter(object):

    @staticmethod
    def convert(pod):
        logging.info('Converting pod for collection level routing: {}'.format(
            pod.root))

        for collection in pod.list_collections():
            conv_collection = ConversionCollection(pod, collection)
            conv_collection.convert()
