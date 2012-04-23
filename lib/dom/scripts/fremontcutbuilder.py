#!/usr/bin/python
# Copyright (c) 2011, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import database
import databasebuilder
import idlparser
import logging.config
import os.path
import sys

# TODO(antonm): most probably should go away or be autogenerated on IDLs roll.
DEFAULT_FEATURE_DEFINES = [
    # Enabled Chrome WebKit build.
    'ENABLE_3D_PLUGIN',
    'ENABLE_3D_RENDERING',
    'ENABLE_ACCELERATED_2D_CANVAS',
    'ENABLE_BATTERY_STATUS',
    'ENABLE_BLOB',
    'ENABLE_BLOB_SLICE',
    'ENABLE_CALENDAR_PICKER',
    'ENABLE_CHANNEL_MESSAGING',
    'ENABLE_CSS_FILTERS',
    'ENABLE_CSS_IMAGE_SET',
    'ENABLE_CSS_SHADERS',
    'ENABLE_DART',
    'ENABLE_DATA_TRANSFER_ITEMS',
    'ENABLE_DETAILS',
    'ENABLE_DEVICE_ORIENTATION',
    'ENABLE_DIRECTORY_UPLOAD',
    'ENABLE_DOWNLOAD_ATTRIBUTE',
    'ENABLE_ENCRYPTED_MEDIA',
    'ENABLE_FILE_SYSTEM',
    'ENABLE_FILTERS',
    'ENABLE_FULLSCREEN_API',
    'ENABLE_GAMEPAD',
    'ENABLE_GEOLOCATION',
    'ENABLE_GESTURE_EVENTS',
    'ENABLE_INDEXED_DATABASE',
    'ENABLE_INPUT_SPEECH',
    'ENABLE_INPUT_TYPE_COLOR',
    'ENABLE_INPUT_TYPE_DATE',
    'ENABLE_JAVASCRIPT_DEBUGGER',
    'ENABLE_JAVASCRIPT_I18N_API',
    'ENABLE_LEGACY_NOTIFICATIONS',
    'ENABLE_LINK_PREFETCH',
    'ENABLE_MEDIA_SOURCE',
    'ENABLE_MEDIA_STATISTICS',
    'ENABLE_MEDIA_STREAM',
    'ENABLE_METER_TAG',
    'ENABLE_MHTML',
    'ENABLE_MUTATION_OBSERVERS',
    'ENABLE_NOTIFICATIONS',
    'ENABLE_OVERFLOW_SCROLLING',
    'ENABLE_PAGE_POPUP',
    'ENABLE_PAGE_VISIBILITY_API',
    'ENABLE_POINTER_LOCK',
    'ENABLE_PROGRESS_TAG',
    'ENABLE_QUOTA',
    'ENABLE_REGISTER_PROTOCOL_HANDLER',
    'ENABLE_REQUEST_ANIMATION_FRAME',
    'ENABLE_RUBY',
    'ENABLE_SANDBOX',
    'ENABLE_SCRIPTED_SPEECH',
    'ENABLE_SHADOW_DOM',
    'ENABLE_SHARED_WORKERS',
    'ENABLE_SMOOTH_SCROLLING',
    'ENABLE_SQL_DATABASE',
    'ENABLE_STYLE_SCOPED',
    'ENABLE_SVG',
    'ENABLE_SVG_FONTS',
    'ENABLE_TOUCH_EVENTS',
    'ENABLE_V8_SCRIPT_DEBUG_SERVER',
    'ENABLE_VIDEO',
    'ENABLE_VIDEO_TRACK',
    'ENABLE_VIEWPORT',
    'ENABLE_WEBGL',
    'ENABLE_WEB_AUDIO',
    'ENABLE_WEB_INTENTS',
    'ENABLE_WEB_SOCKETS',
    'ENABLE_WEB_TIMING',
    'ENABLE_WORKERS',
    'ENABLE_XHR_RESPONSE_BLOB',
    'ENABLE_XSLT',
]

# TODO(antonm): Remove this filter.
UNSUPPORTED_FEATURES = [ 'ENABLE_WEB_INTENTS', 'ENABLE_NOTIFICATIONS' ]

def build_database(idl_files, database_dir, feature_defines = None):
  """This code reconstructs the FremontCut IDL database from W3C,
  WebKit and Dart IDL files."""
  current_dir = os.path.dirname(__file__)
  logging.config.fileConfig(os.path.join(current_dir, "logging.conf"))

  db = database.Database(database_dir)

  # Delete all existing IDLs in the DB.
  db.Delete()

  builder = databasebuilder.DatabaseBuilder(db)

  # TODO(vsm): Move this to a README.
  # This is the Dart SVN revision.
  webkit_revision = '1060'

  # TODO(vsm): Reconcile what is exposed here and inside WebKit code
  # generation.  We need to recheck this periodically for now.
  webkit_defines = [ 'LANGUAGE_DART', 'LANGUAGE_JAVASCRIPT' ]
  if feature_defines is None:
      feature_defines = DEFAULT_FEATURE_DEFINES

  webkit_options = databasebuilder.DatabaseBuilderOptions(
      idl_syntax=idlparser.WEBKIT_SYNTAX,
# TODO(vsm): What else should we define as on when processing IDL?
      idl_defines=[define for define in webkit_defines + feature_defines if define not in UNSUPPORTED_FEATURES],
      source='WebKit',
      source_attributes={'revision': webkit_revision},
      type_rename_map={
        'BarInfo': 'BarProp',
        'DedicatedWorkerContext': 'DedicatedWorkerGlobalScope',
        'DOMApplicationCache': 'ApplicationCache',
        'DOMCoreException': 'DOMException',
        'DOMFormData': 'FormData',
        'DOMSelection': 'Selection',
        'DOMWindow': 'Window',
        'SharedWorkerContext': 'SharedWorkerGlobalScope',
        'WorkerContext': 'WorkerGlobalScope',
      })

  optional_argument_whitelist = [
      ('CSSStyleDeclaration', 'setProperty', 'priority'),
      ('IDBDatabase', 'transaction', 'mode'),
      ]

  # Import WebKit IDLs.
  for file_name in idl_files:
    builder.import_idl_file(file_name, webkit_options)

  # Import Dart idl:
  dart_options = databasebuilder.DatabaseBuilderOptions(
    idl_syntax=idlparser.FREMONTCUT_SYNTAX,
    source='Dart',
    rename_operation_arguments_on_merge=True)

  builder.import_idl_file(
      os.path.join(current_dir, '..', 'idl', 'dart', 'dart.idl'),
      dart_options)

  # Merging:
  builder.merge_imported_interfaces(optional_argument_whitelist)

  builder.fix_displacements('WebKit')

  # Cleanup:
  builder.normalize_annotations(['WebKit', 'Dart'])

  db.Save()

def main():
  current_dir = os.path.dirname(__file__)

  webkit_dirs = [
    'css',
    'dom',
    'fileapi',
    'html',
    'html/canvas',
    'inspector',
    'loader',
    'loader/appcache',
    'Modules/battery',
    'Modules/filesystem',
    'Modules/geolocation',
    'Modules/indexeddb',
    'Modules/mediastream',
    'Modules/speech',
    'Modules/webaudio',
    'Modules/webdatabase',
    'Modules/websockets',
    'notifications',
    'page',
    'plugins',
    'storage',
    'svg',
    'workers',
    'xml',
    ]

  ignored_idls = [
    'AbstractView.idl',
    ]

  idl_files = []

  webcore_dir = os.path.join(current_dir, '..', '..', '..',
                             'third_party', 'WebCore')
  if not os.path.exists(webcore_dir):
    raise RuntimeError('directory not found: %s' % webcore_dir)

  def visitor(arg, dir_name, names):
    for name in names:
      file_name = os.path.join(dir_name, name)
      (interface, ext) = os.path.splitext(file_name)
      if ext == '.idl' and name not in ignored_idls:
        idl_files.append(file_name)

  for dir_name in webkit_dirs:
    dir_path = os.path.join(webcore_dir, dir_name)
    os.path.walk(dir_path, visitor, None)

  database_dir = os.path.join(current_dir, '..', 'database')
  return build_database(idl_files, database_dir)

if __name__ == '__main__':
  sys.exit(main())
