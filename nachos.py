from flask import Flask, Response, request, abort
from xml.dom.minidom import parse, parseString
from xml.parsers.expat import ExpatError
import json
import sys
import os

import config

host = getattr(config, 'host')
port = getattr(config, 'port')
debug = getattr(config, 'debug')
root_dir = getattr(config, 'root_dir')

application = Flask(__name__)

@application.route('/<filename>', methods=['GET'])
@application.route('/<path:path>/<filename>', methods=['GET'])
def parse_smil_get(filename, path = ''):
    smil_file = os.path.join(root_dir, path, filename)
    application.logger.debug('SMIL file full path found ' + smil_file)

    try:
        data = parse(smil_file)
    except IOError as e:
        application.logger.warn("I/O error({0}): {1}".format(e.errno, e.strerror))
        abort(404)
    except ExpatError as e:
        application.logger.error('Error parsing SMIL: ExpatError({0}): {1}'.format(e.code, e.message))
        abort(502)
    except Exception as e:
        application.logger.error('Unexpected exception: {0}'.format(e.message), exc_info=True)
        abort(502)

    data_json = {'sequences': []}
    sources = data.getElementsByTagName('video')
    for elem in sources:
        src = elem.attributes['src'].value
        mp4 = os.path.join(root_dir, src.split(':')[1])
        application.logger.debug('Source file found in smil: ' + mp4)
        clip = { 'clips': [ { 'type': 'source', 'path': mp4 } ] }
        data_json['sequences'].append(clip)

    application.logger.debug('JSON prepared: ' + json.dumps(data_json))
    return Response(json.dumps(data_json), mimetype='application/json')


@application.route('/<filename>', methods=['POST'])
@application.route('/<path:path>/<filename>', methods=['POST'])
def parse_smil_post(filename, path = ''):
    smil_data = request.get_data()
    smil_file = os.path.join(path, filename)
    application.logger.info('Received SMIL via POST path {} request {} bytes'.format(smil_file, len(smil_data)))

    response = Response()

    try:
        data = parseString(smil_data)
        data_json = {'sequences': []}
        sources = data.getElementsByTagName('video')
        for elem in sources:
            src = elem.attributes['src'].value
            mp4 = os.path.join('/', path, src.split(':')[1])
            application.logger.debug('Source file found in smil: ' + mp4)
            clip = { 'clips': [ { 'type': 'source', 'path': mp4 } ] }
            data_json['sequences'].append(clip)
            application.logger.debug('JSON prepared: ' + json.dumps(data_json))
            response.set_data(json.dumps(data_json))
            response.mimetype = 'application/json'
            response.status_code = 200

    except ExpatError as e:
        application.logger.error('Error parsing SMIL: ExpatError({0}): {1}'.format(e.code, e.message))
        response.status_code = 502

    except Exception as e:
        application.logger.error('Unexpected exception: {0}'.format(e.message), exc_info=True)
        response.status_code = 502

    return response


@application.route('/')
def default_route():
    response = Response()
    response.status_code = 404
    return response


if __name__ == "__main__":
    application.run(debug=debug, host=host, port=port)

