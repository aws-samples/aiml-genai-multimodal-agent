# Generative AI and Multi-Modal Agents in AWS: The Key to Unlocking New Value in Financial Markets

This is the code repo of the blog [Generative AI and Multi-Modal Agents in AWS: The Key to Unlocking New Value in Financial Markets](https://www.amazon.com).

This file walks you through how to set up the infrastructure and applications, and run the code to create a multi-modal agents. The blog post provides a detailed discussion of this solution. 

## Architecture Diagram

<img src="images/architecture-diagram.png" width="680"/>


## Prerequisites

This solution uses five [Lambda functions](https://aws.amazon.com/lambda/), which are serverless, event-driven compute services that runs applications. The Python code for the applications are packaged as zip files, stored in *lambda_zip_files* in this repo. We need to add them to an S3 bucket in your account in order to set up the Lambda functions.

First, make an S3 bucket. Go to S3 page in AWS, click "Create bucket". Then enter a bucket name, which should be universally unique. Take a note of the name, because we will need it in another section. Leave the rest as default, and click "Create bucket" at the bottom of the page.

<img src="images/create_bucket.png" width="680"/>


Once the bucket is created, click the bucket name, and create a folder called *code*. To create a folder, click "Create folder", and then enter the folder name "code", then click "Submit".

<img src="images/create_folder.png" width="680"/>

<img src="images/enter_folder_name.png" width="680"/>

Upload the five zip files in folder *lambda_zip_files* to the S3 bucket. 

<img src="images/upload_files.png" width="680"/>

<img src="images/select_files.png" width="680"/>


## Create infrastructure using CloudFormation

[AWS CloudFormation](https://aws.amazon.com/cloudformation/) allows you to create infrasturecture as code. 

First, download the CloudFormation template *cloudformation.yaml*. 

Then upload it in CloudFormation to create a stack. This stack sets up the necessary infrastructure, such as IAM roles and Lambda functions. Go to CloudFormation console in AWS, click Stacks -> Create stack -> With new resources (standard). 

<img src="images/create_stack.png" width="680"/>

Upload *cloudformation.yaml*, and click "Next". 

<img src="images/upload_stack.png" width="680"/>


On the "Specify stack details" page, 

Give the Stack a name, such as "multimodal-cf". Take a note of this name as we will need it when running the app. Change the "SourceCodeBucket" to the name of the S3 bucket you created above.

<img src="images/specify_stack_details.png" width="680"/>

Leave the rest as default. Check the acknowledgement box on the last page and submit it. 

It takes a few minutes to create. Once it is created, you can check the generated resources by clicking on Stacks -> Stack Name. Then click "Resources". The example below shows that the AudioTranscriptsSourceBucketResource is an S3 bucket with the bucket name "test-cf-stack-audiotranscriptssourcebucketresourc-1kg41ts9dy7hk".

<img src="images/stack_resources.png" width="680"/>


## Open SageMaker Notebook Instance

The CloudFormation stack creates a SageMaker Notebook instance that we can use to run the .ipynb file. 

Go to SageMaker page, and click Notebook -> Notebook instances. You will see a Notebook instance named "MultiModalSagemakerInstance". Click "Open jupyter" next to it.

<img src="images/open_jupyter_instance.png" width="600"/>


## Pull in the code

On Jupyter Notebook, click New -> Terminal. This opens a command-line interface.

Copy and paste the following command lines to pull the code from Github.

```
cd SageMaker
git init
git clone git@github.com:aws-samples/aiml-genai-multimodal-agent.git
```
Then open *aiml-genai-multimodal-agent/multimodal-demo.ipynb* Python Notebook. This Notebook has the code to run the solution, as well as explanations of each step. 

# Congratulations! After completing the Jupyter Notebook, you've developed a Multi-Modal Agent! 

If you are interested in further developing a User Interface (UI) on top of it, please continue the following steps.

## Streamlit Application

The Streamlit App for this prioject is located in *app_complete.py*.
It uses dependencies located in the *utility* folder.

In the previous steps, we used SageMaker Notebook for a light-weight set up. However, Streamlit performs better on SageMaker Studio based on our experience, so the front-end app will be using Streamlit App.

First, follow the following steps to set up the SageMaker Studio. 

* [Set Up SageMaker Studio](https://docs.aws.amazon.com/sagemaker/latest/dg/onboard-quick-start.html)
* [Launch SageMaker Studio](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-launch.html)
* [Clone this git repo into studio](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-tasks-git.html)

Then follow the steps below to start the Streamlit Application.

* Change the values for the variables `REGION` and `STACK_NAME` to the region you are working in and name of the deployed cloudformation stack respectively in both `app_complete.py` and `app_complete2.py`
* Open a system terminal by clicking on **Amazon SageMaker Studio** and then **System Terminal** as shown in the diagram below
* <img src="images/studio-new-launcher.png" width="600"/>
* Navigate into the cloned repository directory using the `cd` command and run the command `pip install -r requirements.txt` to install the needed python libraries
* Run command `python3 -m streamlit run app_complete.py` to start the Streamlit server. Do not use the links generated by the command as they won't work in studio.
* To enter the Streamlit app, open and run the Streamlit_app.ipynb notebook. This will generate the appropiate link to enter your Streamlit app from SageMaker studio. Click on the link to enter your Streamlit app. Happy querying :)
* **⚠ Note:**  If you rerun the Streamlit server it may use a different port. Take not of the port used (port number is the last 4 digit number after the last :) and modify the `port` variable in the `Streamlit_app.ipynb` notebook to get the correct link.

## You've made it very far! If you would keep going and run it on AWS EC2, please follow the following steps.

To run this Streamlit App on AWS EC2 (I tested this on the Ubuntu Image)
* [Create a new ec2 instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html)
* Expose TCP port range 8500-9000 on Inbound connections of the attached Security group to the ec2 instance. TCP port 8501 is needed for Streamlit to work. See image below
* <img src="images/sg-rules.PNG" width="600"/>
* [Connect to your ec2 instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstances.html)
* Run the appropiate commands to update the ec2 instance (`sudo apt update` and `sudo apt upgrade` -for Ubuntu)
* Clone this git repo 
* Change the values for the variables `REGION` and `STACK_NAME` to the region you are working in and name of the deployed cloudformation stack respectively in both `app_complete.py` and `app_complete2.py`. Make use of the `nano` command to make this changes. e.g. `nano app_complete.py`
* Install python3 and pip if not already installed
* Install the dependencies in the requirements.txt file by running the command `sudo pip install -r requirements.txt`
* Run command `python3 -m streamlit run app_complete.py` 
* Copy the external link and paste in a new browser tab

There are two different UI styles for this app. Depending on what you like, either use the app `app_complete.py` or `app_complete2.py`.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

