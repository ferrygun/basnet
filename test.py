import io
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import numpy as np
import time
from datetime import datetime

import logging
import argparse
import requests

# Initialize the Flask application.
app = Flask(__name__)
CORS(app)


# The paste endpoints handles new paste requests.
@app.route('/paste', methods=['POST'])
def paste():
	start = time.time()
	logging.info(' CUT')
	print("here")

	# Convert string of image data to uint8.
	if 'data' not in request.files:
		return jsonify({
			'status': 'error',
			'error': 'missing file param `data`'
		}), 400
	data = request.files['data'].read()
	if len(data) == 0:
		return jsonify({'status:': 'error', 'error': 'empty image'}), 400


	# Save debug locally.
	with open('imgtmp.jpg', 'wb') as f:
		f.write(data)

	image = Image.open("imgtmp.jpg")
	print(image.size)

	files= {'data': open('imgtmp.jpg', 'rb')}
	headers = {}
	res = requests.post('http://localhost:8080', headers=headers, files=files )
	#res = requests.post('http://u2net-predictor.tenant-compass.global.coreweave.com', headers=headers, files=files ) #img size 320x320

	# Save mask locally.
	logging.info(' > saving results...')
	with open('cut_mask.png', 'wb') as f:
		f.write(res.content)

	#logging.info(' > opening mask...')
	mask = Image.open('cut_mask.png').convert("L")
	print(mask.size[0])
	# Convert string data to PIL Image.
	#logging.info(' > compositing final image...')
	ref = Image.open(io.BytesIO(data)).resize((mask.size[0],mask.size[1]))
	#ref = Image.open(io.BytesIO(byteImg)).resize((320,320))
	empty = Image.new("RGBA", ref.size, 0)
	img = Image.composite(ref, empty, mask)

	# TODO: currently hack to manually scale up the images. Ideally this would
	# be done respective to the view distance from the screen.
	img_scaled = img.resize((img.size[0] * 3, img.size[1] * 3))
	#print(img.size[1], img.size[0])
	#img_scaled = img.resize((img.size[1], img.size[0]), resample=Image.BILINEAR)

	# Save locally.
	#logging.info(' > saving final image...')
	img_scaled.save('cut_current.png')
	img.save('cut_current1.png')

	# Save to buffer
	buff = io.BytesIO()
	img.save(buff, 'PNG')
	buff.seek(0)

	return send_file(buff, mimetype='image/png')
	

if __name__ == '__main__':
    os.environ['FLASK_ENV'] = 'development'
    port = int(os.environ.get('PORT', 8081))
    app.run(debug=True, host='0.0.0.0', port=port)