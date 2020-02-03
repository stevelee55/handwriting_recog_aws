# Import libraries.
import sys
sys.path.append("./packages")
import onnxruntime as rt
import numpy as np
from PIL import Image
from datetime import datetime
import boto3

lambda_tmp_directory = "/tmp"
s3_bucket_name = "<your-unique-s3-bucket-name>"
model_file_name = "model.onnx"
input_file_name = "digit.png"
temp_resized_input_file_name = "resized_" + input_file_name
output_file_name = "results.txt"


def lambda_handler(event, context):
    
    # Download test image and model from s3.
    client = boto3.client('s3')
    client.download_file(s3_bucket_name, input_file_name, lambda_tmp_directory + "/" + input_file_name)
    client.download_file(s3_bucket_name, model_file_name, lambda_tmp_directory + "/" + model_file_name)
    
    # Download image and model to disk.
    
    # from PilLite import Image
    img = Image.open(lambda_tmp_directory + "/" + input_file_name)
    new_img = img.resize((28, 28), Image.BICUBIC)
    new_img.save(lambda_tmp_directory + "/" + temp_resized_input_file_name, quality=100)
    
    # Preprocessing of the image.
    new_img = Image.open(lambda_tmp_directory + "/" + temp_resized_input_file_name).convert("L")
    new_img = np.asarray(new_img).astype("float32")
    new_img /= 256
    
    #print(new_img)
    new_img = new_img.reshape(-1,1,28,28)
    #print(new_img)
    
    # Create session.
    sess = rt.InferenceSession(lambda_tmp_directory + "/" + model_file_name)
    input_name = sess.get_inputs()[0].name
    output_name = sess.get_outputs()[0].name
    pred_onx = sess.run([output_name], {input_name: new_img})[0]
    print(pred_onx)
    
    from scipy.special import softmax
    result = np.array(pred_onx).tolist()
    #print(result)
    scores = softmax(result[0], axis=0)
    scores = np.squeeze(scores)
    # print(np.argmax(scores))
    print(scores)
    
    a = np.argsort(scores)[::-1]
    print(a)
    nums = [0,1,2,3,4,5,6,7,8,9]

    # Start creating output file.
    f = open(lambda_tmp_directory + "/" + output_file_name, "w+")

    for i in a[0:10]:
    	# print('class=%s ; probability=%f' %(nums[i],scores[i]))
        f.write('class=%s ; probability=%f \n' %(nums[i],scores[i]))
    f.close()

    # Get today's date and append to the file name.
    current_date_time = str(datetime.now())
    # Upload the created file to the s3 bucket.
    client.upload_file(lambda_tmp_directory + "/" + output_file_name, s3_bucket_name, output_file_name)
