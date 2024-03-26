import logging
import azure.functions as func
import json
import azure.storage.blob
import base64
#import requests
import time
import os


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_trigger_func1")
def http_trigger_func1(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        body = json.dumps(req.get_json())
        if body:
            logging.info(body)
            values = json.loads(body = json.dumps(req.get_json()))['values']
            for value in values:
                assert ('data' in value), "'data' field is required."
                data = value['data']  
                blob_name =  data['title']

                conn_string = os.environ["CONNECTION_STRING"]
                blob_service_client = azure.storage.blob.BlobServiceClient.from_connection_string(conn_string)
                container_name = os.environ["CONTAINER_NAME"]
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
                blob_content = blob_client.download_blob().readall()

                #print(blob_content)

                doc_intel_endpoint = os.environ["DOC_INTEL_ENDPOINT"]
                doc_intel_key = os.environ["DOC_INT_KEY"]
                doc_intel_modelId = os.environ["DOC_INTEL_MODELID"]
                doc_intel_apiVersion = os.environ["DOC_INTEL_API_VERSION"]

                # get balancete via Forms Recognizer (Document Analysis)
                endpoint = doc_intel_endpoint
                modelId = doc_intel_modelId
                api_version = doc_intel_apiVersion

                url = (
                    f"{endpoint}/formrecognizer/documentModels/{modelId}"
                    f":analyze?api-version={api_version}"
                )

                
                headers = {
                # Request headers
                'Content-Type': 'application/json',
                'Ocp-Apim-Subscription-Key': doc_intel_key,
                    }


                base64_content = base64.b64encode(blob_content).decode('utf-8')
                body = {
                    "base64Source": base64_content
                }
                body_json = json.dumps(body)

                
                response = req.post(url,
                                    data = body_json,
                                    headers = headers)
                
                logging.info(f"response {response}")
                logging.info(f"response text  {response.text}")
                logging.info(f"response headers {response.headers}")

                #return func.HttpResponse(f"Hello, this message from Azure : {response} and {response.headers}",status_code=200)
                if response.status_code != 202:
                    logging.warning(f"não tem response {response.text}")
                    
                    print("POST analyze failed:\n%s" % response.text)
                    quit()
                else:
                    print(response.headers["Operation-Location"])
                    operation_url = response.headers["Operation-Location"]
                    # print(f"Analysis started. Operation URL: {operation_url}")

                    wait_sec = 25
                    time.sleep(wait_sec)

                    #operation_url = 'https://docintelligence-poc-gen-ai.cognitiveservices.azure.com/formrecognizer/documentModels/prebuilt-read/analyzeResults/de32bdcf-c8a6-421b-aca9-58625c18ec86?api-version=2023-07-31'

                    while True:
                        
                        #response = requests.get(operation_url, headers=headers)
                        response = req.get(operation_url, headers={"Ocp-Apim-Subscription-Key": doc_intel_key})
                        print("response\n",response)
                        try:
                            status = response.json()["status"]
                        except Exception:
                            print("formato invalido")

                        if status == "succeeded":
                            logging.info("entrou no succeeded")
                            print("Analysis completed successfully.")
                            result = response.json()

                            return func.HttpResponse(f"Hello, this message from Azure : {result}",status_code=200)
                    
                        elif status == "failed":
                            logging.info("entrou no failed")
                            raise Exception
                            #print("Analysis failed.")
                            #raise DocIntelligenceException.get_error_statusFailed()
                        elif status == "running":
                            logging.info("entrou no running")
                            continue
                            #print("Analysis is still running. \
                            #    Checking again in a few seconds...")
                            time.sleep(5)
                        else:
                            print(f"Unknown status: {status}")
                            #raise DocIntelligenceException.get_error_statusUnknown()
        else:
            return func.HttpResponse(
                "Invalid body",
                status_code=400
            )
    except ValueError:
        return func.HttpResponse(
             "Invalid body",
             status_code=400
        )

    
 

    #response = requests.get(operation_url, headers=headers)
    #result = response.json()
    """
    resp_json = json.loads(response.text)
    status = resp_json["status"]    

    #status = response.json()["status"]

    if status == "succeeded":
        print("POST Layout Analysis succeeded:\n%s")
        results = resp_json
    else:
        print("GET Layout results failed:\n%s")
        quit()

    results = resp_json


    """ 
