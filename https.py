import requests
import subprocess
import sys
from PIL import Image
from io import BytesIO

api_url='https://westus.api.cognitive.microsoft.com/vision/v1.0/ocr'

header = {'Ocp-Apim-Subscription-Key': '6b360cc90f064ddcac8af790289a641e',
          'Content-Type': 'application/octet-stream'}

params = {'language': 'unk'}

try:
    # Retrieve the binary image data from the clipboard
    p = subprocess.run('/Users/chunkauwong/Desktop/WTH/1.jpg',
                       shell=True,
                       check=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    img_data = p.stdout

    img = Image.open(BytesIO(img_data))
    # Ensure the image is at least 40x40
    if min(img.size) < 40:
        img = img.crop((0, 0, max(img.size[0], 40), max(img.size[1], 40)))

    bin_img = BytesIO()
    img.save(bin_img, format='PNG')
    img.close()

    img_data = bin_img.getvalue()
    bin_img.close()

    r = requests.post(api_url,
                      params=params,
                      headers=header,
                      data=img_data)

    print r.raise_for_status()

    data = r.json()
    print data
    text = ''
    for item in r.json()['regions']:
        for line in item['lines']:
            for word in line['words']:
                text += ' ' + word['text']
            text += '\n'
    print(text)

except subprocess.CalledProcessError as e:
    pass
    #print('Could not get image from clipboard: {}'.format(e), file=sys.stderr)

except requests.HTTPError as e:
    pass
    #print('HTTP error occurred: {}'.format(e), file=sys.stderr)

except Exception as e:
    pass
    #print('Error occurred: {}'.format(e), file=sys.stderr)
