import os
import board
import RPi.GPIO as GPIO
from azure.storage.blob import ContentSettings, BlobClient
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials
from PIL import ImageDraw
from PIL import Image
import matplotlib.pyplot as plt

def main():
    try:
        # custom vision api
        credentials = ApiKeyCredentials(in_headers={"Prediction-key": "your prediction key"})
        predictor = CustomVisionPredictionClient("your prediction endpoint", credentials)
        projectID = "your project ID"
        publish_iteration_name="your iteration number"
        #Bolb Storage
        conn_str="your blob storage connetion string"
        container_name="your container name"
        blob_name="your bolb name"
        # Initialize GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()
        GPIO.setup(4, GPIO.IN) #PIR
        print("Detection started. Press Ctrl-C to exit")

        while True:
            if GPIO.input(4): #motion detected
                try:                                  
                    # capture the image with USB webcamera
                    a=os.system("fswebcam --no-banner -r 1280x720 capture.jpg")
                    print(a)
                    # open and detect the captured image
                    with open("capture.jpg", mode="rb") as captured_image:
                        results = predictor.detect_image(projectID, publish_iteration_name, captured_image)
    
                    # Display the results.
                    for prediction in results.predictions:                       
                        if prediction.probability>0.9:
                            print("\t" + prediction.tag_name + ": {0:.2f}%".format(prediction.probability * 100))
                            bbox = prediction.bounding_box
                            im = Image.open("capture.jpg")
                            draw = ImageDraw.Draw(im)
                            draw.rectangle([int(bbox.left * 1280), int(bbox.top * 720), int((bbox.left + bbox.width) * 1280), int((bbox.top + bbox.height) * 720)],outline='red',width=5)
                            im.save("detect.jpg")
					# show images
                    #de=Image.open("detect.jpg")                    
					#plt.figure("Result")
                    #plt.imshow(de)
                    #plt.show()
                    
                    # upload the image to Azure Blob Storage, Overwrite if it already exists!
                    blob = BlobClient.from_connection_string(conn_str, container_name, blob_name)
                    image_content_setting = ContentSettings(content_type='image/jpeg')
                    with open("detect.jpg", "rb") as data:
                        blob.upload_blob(data,overwrite=True,content_settings=image_content_setting)
                        print("Upload completed")
                except KeyboardInterrupt:
                    print("Detection stopped")
                    GPIO.cleanup()
                    break
    except Exception as error:
        print(error.args[0])

if __name__ == '__main__':
    main()