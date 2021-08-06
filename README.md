# Sentimental-Analysis-of-Financial-reports

This project is about taking financial reports and extracting, preprocessing and performing sentiment analysis on it. 
## Data-set description
The dataset used is provided by [US Securities and Exchange Commision](https://www.sec.gov/os/accessing-edgar-data). 
This [dataset](https://github.com/sanjuGoudru/Sentimental-Analysis-of-Financial-reports/blob/main/cik_list.xlsx) contains unique id, company name and link to find the report.
## Data Extraction
Data Extraction phase consists of using the link provided to download financial report and saving it in [Input_dir](https://github.com/sanjuGoudru/Sentimental-Analysis-of-Financial-reports/tree/main/input_dir). This step is done by function save_text_in_url() in [Process_data class](https://github.com/sanjuGoudru/Sentimental-Analysis-of-Financial-reports/blob/main/Process_data.py).

Note: Since the website https://www.sec.gov/ has threshold capacity, so downloading all the files will take lot of time.
## Data Preprocessing
Things done in this phase:
1. All the text is converted to lower case
1. Remove all non-alpha characters except newline and full-stop(end of sentence character)
1. Replace mulitple spaces with single space
1. Remove blank lines
1. Remove stop words
## Sentiment analysis
1. Calculate positive score,negative score by identifying those words from list of sentimental words obtained from [Master Dictionary and Sentiment Word Lists](https://sraf.nd.edu/textual-analysis/resources/#Master%20Dictionary)
1. Derivwe polarity score from calculated positive score and negative score
1. Also many other variables are calculated like average sentence length, percentage of complex words, fog index, uncertaininty score, constraint score, positive and negative word proportion.
## Code snippet to run:

Step1: Import required class:

```
from Process_data import Process_data
import pandas as pd
```
Step2: Read excel file as DataFrame
```
df = pd.read_excel('cik_list.xlsx')
```
Step3: Create object of the class
```
obj = Process_data(df)
```
Step4: Download files in ‘input_dir’ folder. If the parameter num is None then whole 152 records are downloaded, Else specified number of records will be download.
```
ex.download_files(num=None)
```
Step5: Compute the required parameters and convert it into DataFrame form. The parameter num works same as above step.
```
res_df = ex.compute(num=None)
```
Step6: Convert dataframe to output csv file
```
res_df.to_csv(‘output_data.csv’)
```
