import time
import os
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
import re
import signal
import sys
import glob
from langchain_community.llms import HuggingFaceHub

# Set up environment variables
os.environ["HUGGINGFACEHUB_API_TOKEN"] = <HUGGINGFACE_API_TOKEND>
os.environ["PINECONE_API_KEY"] = <PINCONE_API_KEY>
os.environ["PINECONE_ENVIRONMENT"] = "us-east1-aws" 

# RAG Class
class RAG_HUGGINGFACE:
    def __init__(self, embedding_model="sentence-transformers/multi-qa-MiniLM-L6-cos-v1", 
                 llm_model="mistralai/Mistral-7B-Instruct-v0.3", 
                 rag_prompt="rlm/rag-prompt", 
                 csv_paths=None,
                 index_name="nugget"):
        
        """
        Define all models and data
        """

        self.vectorstore = None
        self.qa_chain = None
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.rag_prompt = rag_prompt
        self.csv_paths = csv_paths if isinstance(csv_paths, list) else [csv_paths]
        self.index_name = index_name
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model)
        self.document_embeddings = None
        self.document_texts = None

        signal.signal(signal.SIGINT, self.cleanup)

    def cleanup(self, *args):
        """
        Cleanup resources before exiting.
        """
        sys.exit(0)

    def load_csv_files(self):
        """Load data from multiple CSV files and convert to document format"""

        all_documents = []
        
        for csv_path in self.csv_paths:
            try:
                df = pd.read_csv(csv_path)
                file_name = os.path.basename(csv_path)
                df['source_file'] = file_name
                for idx, row in df.iterrows():
                    metadata = {col: str(row[col]) for col in df.columns}
                    content_parts = []
                    for col in df.columns:
                        if col != 'source_file':  
                            content_parts.append(f"{col}: {row[col]}")
                    content = "\n".join(content_parts)
                    doc = Document(page_content=content, metadata=metadata)
                    all_documents.append(doc)
            except Exception as e:
                continue
        
        print(f"Total documents loaded from all CSV files: {len(all_documents)}")
        return all_documents

    def split_texts(self, documents, chunk_size=500, chunk_overlap=50):
        """Split documents into chunks for processing"""

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        splits = text_splitter.split_documents(documents)
        return splits

    def embedding_and_vector(self, splits):
        """
        Embedding chunks
        """

        start_time = time.time()
        vectorstore = Pinecone.from_documents(
            documents=splits,
            embedding=self.embeddings,
            index_name=self.index_name,
        )
        
        end_time = time.time()
        print(f"Embedding completed in {end_time - start_time:.2f} seconds.")
        
        return vectorstore

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def qa_chain_model(self, vectorstore):
        
        start_time = time.time()
        llm = HuggingFaceHub(
            repo_id=self.llm_model,
            huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
            task="text-generation",
            model_kwargs={
                "temperature": 0.1,
                "top_p": 0.95,
                "max_length": 200,
                "do_sample": True
            }
        )
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 3}
        )

        rag_prompt = hub.pull(owner_repo_commit=self.rag_prompt)
        qa_chain = (
            {"context": retriever | self.format_docs, "question":
            RunnablePassthrough()}
            | rag_prompt
            | llm
            | StrOutputParser()
        )

        end_time = time.time()
        print(f"QA Chain setup complete in {end_time - start_time:.2f} seconds.")

        return qa_chain

    def train_rag(self):

        if not self.csv_paths:
            raise ValueError("CSV paths must be specified")
            
        documents = self.load_csv_files()
        if not documents:
            raise ValueError("No documents loaded from CSV files")
            
        
        splits = self.split_texts(documents)
        
        self.document_texts = [doc.page_content for doc in splits]
        self.document_embeddings = self.embeddings.embed_documents(self.document_texts)

        self.vectorstore = self.embedding_and_vector(splits=splits)
        
        self.qa_chain = self.qa_chain_model(vectorstore=self.vectorstore)

    def response_query(self, question):
        print("Processing query...")

        if self.is_document_related(question):
            start_time = time.time()
            answer = self.qa_chain.invoke(question)
            end_time = time.time()
            return answer
        else:
            return self.ask_general_huggingface(question)

    def is_document_related(self, question, threshold=0.3):

        question_embedding = self.embeddings.embed_documents([question])
        similarities = cosine_similarity(question_embedding, self.document_embeddings)
        
        max_similarity = np.max(similarities)
        
        if max_similarity >= threshold:
            return True
        else:
            return False

    def ask_general_huggingface(self, question):
        return "The question seems to be out of my scope, please change the prompt or add some more context"
    

    def __del__(self):
        print("Destructor called.")
        self.cleanup()


# Gather all csv files (Data)
DEFAULT_CSV_FOLDER = './data'
csv_files = glob.glob(os.path.join(DEFAULT_CSV_FOLDER, '*.csv'))
if not csv_files:
    print(f"No CSV files found in {DEFAULT_CSV_FOLDER}. Please add some data files.")

# Initalizing and training Rag Pipeline
rag_engine = RAG_HUGGINGFACE(
    csv_paths=csv_files,  
    llm_model="mistralai/Mistral-7B-Instruct-v0.3",
    rag_prompt="rlm/rag-prompt",
    index_name="nugget"  
)
rag_engine.train_rag()
