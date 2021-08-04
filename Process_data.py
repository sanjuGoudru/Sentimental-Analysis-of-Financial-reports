import os
import pandas as pd, re
from nltk.tokenize import sent_tokenize,word_tokenize
from bs4 import BeautifulSoup as BS
from pathlib import Path
import requests
import time



class Process_data:
    df_columns = ['CIK', 'CONAME', 'FYRMO', 'FDATE', 'FORM', 'SECFNAME']
    threshold_title = 'Request Rate Threshold Exceeded'
    with open('./StopWords_Generic.txt' ,'r') as stop_words_file:
        stopwords = stop_words_file.read()
        stopwords = stopwords.lower().split(sep='\n')

    with open('./pos_words.txt','r') as pw_f:
        pw=pw_f.read()
        pw_list = pw.split('\n')

    with open('./neg_words.txt','r') as nw_f:
        nw = nw_f.read()
        nw_list = nw.split('\n')

    uncertain_words = list(pd.read_excel('uncertainty_dictionary.xlsx')['Word'])
    uncertain_words = [item.lower() for item in uncertain_words]

    constrain_words = list(pd.read_excel('constraining_dictionary.xlsx')['Word'])
    constrain_words = [item.lower() for item in constrain_words]



    def __init__(self,df):
        if len(df) == 0:
            raise Exception('DataFrame is empty')

        if set(df.columns) != set(self.df_columns):
            raise Exception('DataFrame doesnt have proper columns')

        self.df = df
        self.global_constrain_count,self.global_word_count = 0,0

    def encode_name(self,secfname):
        splitted = secfname.split(sep="/")
        name = "+".join(splitted)
        return name

    def remove_stop_words(self,text):
        word_tokens = word_tokenize(text)
        filtered_data = [w for w in word_tokens if not w in self.stopwords]
        return filtered_data

    def get_positive_score(self,filtered_text_list):
        pw_count = 0
        for word in filtered_text_list:
            if word in self.pw_list:
                pw_count = pw_count + 1
        return pw_count

    def get_negative_score(self,filtered_text_list):
        nw_count = 0
        for word in filtered_text_list:
            if word in self.nw_list:
                nw_count = nw_count + 1
        return nw_count

    def get_polarity_score(self,pos_score, neg_score):
        pol_score = (pos_score - neg_score) / ((pos_score + neg_score) + 0.000001)
        return pol_score

    def get_avg_sentence_length(self,sent_tokens,filtered_text_list):
        sent_len,word_len = len(sent_tokens),len(filtered_text_list)
        if sent_len !=0:
            avg_sent_len = word_len/(1.0*sent_len)
        else:
            avg_sent_len = 0
        return avg_sent_len

    ## Obtained code from https://eayd.in/?p=232
    @staticmethod
    def sylco(word) :

        word = word.lower()

        # exception_add are words that need extra syllables
        # exception_del are words that need less syllables

        exception_add = ['serious','crucial']
        exception_del = ['fortunately','unfortunately']

        co_one = ['cool','coach','coat','coal','count','coin','coarse','coup','coif','cook','coign','coiffe','coof','court']
        co_two = ['coapt','coed','coinci']

        pre_one = ['preach']

        syls = 0 #added syllable number
        disc = 0 #discarded syllable number

        #1) if letters < 3 : return 1
        if len(word) <= 3 :
            syls = 1
            return syls

        #2) if doesn't end with "ted" or "tes" or "ses" or "ied" or "ies", discard "es" and "ed" at the end.
        # if it has only 1 vowel or 1 set of consecutive vowels, discard. (like "speed", "fled" etc.)

        if word[-2:] == "es" or word[-2:] == "ed" :
            doubleAndtripple_1 = len(re.findall(r'[eaoui][eaoui]',word))
            if doubleAndtripple_1 > 1 or len(re.findall(r'[eaoui][^eaoui]',word)) > 1 :
                if word[-3:] == "ted" or word[-3:] == "tes" or word[-3:] == "ses" or word[-3:] == "ied" or word[-3:] == "ies" :
                    pass
                else :
                    disc+=1

        #3) discard trailing "e", except where ending is "le"

        le_except = ['whole','mobile','pole','male','female','hale','pale','tale','sale','aisle','whale','while']

        if word[-1:] == "e" :
            if word[-2:] == "le" and word not in le_except :
                pass

            else :
                disc+=1

        #4) check if consecutive vowels exists, triplets or pairs, count them as one.

        doubleAndtripple = len(re.findall(r'[eaoui][eaoui]',word))
        tripple = len(re.findall(r'[eaoui][eaoui][eaoui]',word))
        disc+=doubleAndtripple + tripple

        #5) count remaining vowels in word.
        numVowels = len(re.findall(r'[eaoui]',word))

        #6) add one if starts with "mc"
        if word[:2] == "mc" :
            syls+=1

        #7) add one if ends with "y" but is not surrouned by vowel
        if word[-1:] == "y" and word[-2] not in "aeoui" :
            syls +=1

        #8) add one if "y" is surrounded by non-vowels and is not in the last word.

        for i,j in enumerate(word) :
            if j == "y" :
                if (i != 0) and (i != len(word)-1) :
                    if word[i-1] not in "aeoui" and word[i+1] not in "aeoui" :
                        syls+=1

        #9) if starts with "tri-" or "bi-" and is followed by a vowel, add one.

        if word[:3] == "tri" and word[3] in "aeoui" :
            syls+=1

        if word[:2] == "bi" and word[2] in "aeoui" :
            syls+=1

        #10) if ends with "-ian", should be counted as two syllables, except for "-tian" and "-cian"

        if word[-3:] == "ian" :
        #and (word[-4:] != "cian" or word[-4:] != "tian") :
            if word[-4:] == "cian" or word[-4:] == "tian" :
                pass
            else :
                syls+=1

        #11) if starts with "co-" and is followed by a vowel, check if exists in the double syllable dictionary, if not, check if in single dictionary and act accordingly.

        if word[:2] == "co" and word[2] in 'eaoui' :

            if word[:4] in co_two or word[:5] in co_two or word[:6] in co_two :
                syls+=1
            elif word[:4] in co_one or word[:5] in co_one or word[:6] in co_one :
                pass
            else :
                syls+=1

        #12) if starts with "pre-" and is followed by a vowel, check if exists in the double syllable dictionary, if not, check if in single dictionary and act accordingly.

        if word[:3] == "pre" and word[3] in 'eaoui' :
            if word[:6] in pre_one :
                pass
            else :
                syls+=1

        #13) check for "-n't" and cross match with dictionary to add syllable.

        negative = ["doesn't", "isn't", "shouldn't", "couldn't","wouldn't"]

        if word[-3:] == "n't" :
            if word in negative :
                syls+=1
            else :
                pass

        #14) Handling the exceptional words.

        if word in exception_del :
            disc+=1

        if word in exception_add :
            syls+=1

        # calculate the output
        return numVowels - disc + syls

    def get_perc_complex_words(self,words):
        count = 0
        for word in words:
            if Process_data.sylco(word)>=2:
                count = count + 1
        if len(words) == 0:
            perc_complex_words = 0
        else:
            perc_complex_words = (100.0*count)/(1.0*len(words))
        return count,perc_complex_words

    def get_fog_index(self,avg_sent_length,perc_complex_words):
        return 0.4 * (avg_sent_length + perc_complex_words)

    def get_uncertainity_score(self,words):
        count = 0
        for word in words:
            if word in self.uncertain_words:
                count += 1
        return count

    def get_constrain_score(self,words):
        count = 0
        for word in words:
            if word in self.constrain_words:
                count += 1
        self.global_constrain_count += count
        self.global_word_count += len(words)
        return count

    def preprocess(self,secfname):
        file_path = './input_dir/' + self.encode_name(secfname)
        with open(file_path,'r', encoding="utf-8") as file:
            data = file.read()
        soup = BS(data,'lxml')
        ## Convert soup text to lowercase
        data = soup.text.lower()
        ## Remove all non-alpha characters except newline and full-stop(end of sentence character)
        data = re.sub(r'[^A-Za-z\n\. ]+', ' ', data)
        ## Replace mulitple spaces with single space
        data = re.sub(' +', ' ', data)
        ## Replace blank lines
        data = re.sub(r'\n+', '\n', data)
        ## tokenize sentences
        sent_tokens = sent_tokenize(data)
        ## Remove full-stop(end of sentence)
        data = re.sub(r'[^A-Za-z\n ]+', ' ', data)
        ## Remove stopwords
        filtered_text_list = self.remove_stop_words(data)
        ## Get positive_score
        pos_score = self.get_positive_score(filtered_text_list)
        ## Get negative score
        neg_score = self.get_negative_score(filtered_text_list)
        ## Get polarity score
        pol_score = self.get_polarity_score(pos_score, neg_score)
        ## Get average sentences length
        avg_sent_length = self.get_avg_sentence_length(sent_tokens,filtered_text_list)
        ## Get percentage of complex words
        complex_word_count,perc_complex_words = self.get_perc_complex_words(filtered_text_list)
        ## Get fog index
        fog_index = self.get_fog_index(avg_sent_length,perc_complex_words)
        ## Calculate word count
        word_count = len(filtered_text_list)
        ## Calculate uncertainity score
        uncertainity_score = self.get_uncertainity_score(filtered_text_list)
        ## Calculate constrain score
        constrain_score = self.get_constrain_score(filtered_text_list)
        ## Calculate Positive word proportion
        if word_count == 0:
            pos_word_proportion = 0
        else:
            pos_word_proportion = pos_score/word_count
        ## Calculate Negative word proportion
        if word_count == 0:
            neg_word_proportion = 0
        else:
            neg_word_proportion = neg_score/word_count
        ## Calculate uncertainity word proportion
        if word_count == 0:
            uncertain_word_proportion = 0
        else:
            uncertain_word_proportion = uncertainity_score/word_count
        ## Calculate constraint proportion
        if word_count == 0:
            constraint_proportion = 0
        else:
            constraint_proportion = constrain_score/word_count

        result = (pos_score,neg_score,pol_score,avg_sent_length,
                  perc_complex_words,fog_index,complex_word_count,
                  word_count,uncertainity_score,constrain_score,
                  pos_word_proportion,neg_word_proportion,neg_word_proportion,
                  constraint_proportion)
        return result

    def get_whole_report_constraint_index(self):
        global_constraint_index = self.global_constrain_count/(1.0*self.global_word_count)
        return global_constraint_index

    def compute(self,num=None):
        new_list = []
        if num is None:
            df = self.df
        else:
            df = self.df.head(num)
        for index, row in df.iterrows():
            secfname = row['SECFNAME']
            result = self.preprocess(secfname)
            new_list.append(result)

        columns = ['pos_score','neg_score','pol_score','avg_sent_length',
                      'perc_complex_words','fog_index','complex_word_count',
                      'word_count','uncertainity_score','constrain_score',
                      'pos_word_proportion','neg_word_proportion','neg_word_proportion',
                      'constraint_proportion']
        res_df = pd.DataFrame(new_list,columns=columns)

        final_df = pd.concat((df,res_df),axis=1)
        final_df['constraining_words_whole_report'] = self.get_whole_report_constraint_index()
        return final_df

    def get_soup(self,url):
        url = url
        headers = {'User-Agent':'Mozilla/5.0'}
        page = requests.get(url)
        soup = BS(page.text, "html.parser")
        return soup

    def save_text_in_url(self,secfname):
        url = 'https://www.sec.gov/Archives/'+secfname
        name_of_file = self.encode_name(secfname)

        my_file = Path('./input_dir/'+name_of_file)
        if my_file.is_file():
            return
        i = 0
        while(True):
            soup = self.get_soup(url)
            ## self.threshold_title not in soup.title
            if soup != None and ((soup.title==None) or (self.threshold_title not in soup.title.text)):
                print(f'IF:Soup title: {soup.title}')
                break
            else:
                print(f'ELSE:Soup title: {soup.title}')
                i = i+1
                time.sleep(i/6.0)
                print(f'{secfname}:{i}')
                continue

        text = soup.get_text()

        with open('./input_dir/'+name_of_file, "w+", encoding="utf-8") as txt_file:
            txt_file.write(text)

    def download_files(self,num=None):
        df = self.df
        if num is not None:
            df = df.head(num)
        for index, row in df.iterrows():
            self.save_text_in_url(row['SECFNAME'])
