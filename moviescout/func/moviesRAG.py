import os
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatLlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.chains import create_history_aware_retriever 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class MovieRecommendationRAG:
    def __init__(self, embedding_model="all-MiniLM-L6-v2", 
                 persist_directory=None, 
                 csv_file_path=None, 
                 tfidf_file_path=None):
        self.chat_history = []

        # Set default paths relative to the current directory
        self.embedding_model = embedding_model
        self.persist_directory = persist_directory or os.path.join(CURRENT_DIR, "..", "..", "models", "chroma_db")
        self.csv_file_path = csv_file_path or os.path.join(CURRENT_DIR, "..", "..", "data", "processed", "TMDB.csv")
        self.tfidf_file_path = tfidf_file_path or os.path.join(CURRENT_DIR, "..", "..", "models", "content.pkl")
        
        # Initialize components
        self.embedding_function = SentenceTransformerEmbeddings(model_name=self.embedding_model)
        self.loader = CSVLoader(self.csv_file_path, encoding="utf-8")
        self.documents = self.loader.load()
        
        self.db = None
        self.llm = None
        
        self._load_or_create_chroma_db()
        self._initialize_llm()

    def _load_or_create_chroma_db(self):
        """Load or create Chroma vector database."""
        if os.path.exists(self.persist_directory):
            self.db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embedding_function)
            print("Existing Chroma database loaded.")
        else:
            self.db = Chroma.from_documents(self.documents, self.embedding_function, persist_directory=self.persist_directory)
            self.db.persist()
            print("New Chroma database created and persisted.")
    
    def _initialize_llm(self):
        """Initialize the LLM model and prompt."""
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        
        self.llm = ChatLlamaCpp(
            model_path=os.path.join(CURRENT_DIR, "..", "..", "models", "Phi-3-mini-4k-instruct-q4.gguf"),
            use_mlock=True,
            callback_manager=callback_manager,
            n_ctx=1024,
            verbose=False,
            n_gpu_layers=48,
            n_threads=16,
            n_batch=512 
        )

        contextualize_q_system_prompt = """
        Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. 
        Do NOT answer the question, just reformulate it if needed and otherwise return it as is.
        """

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        retriever = self.db.as_retriever(search_kwargs={"k": 1})

        history_aware_retriever = create_history_aware_retriever(
            self.llm,  
            retriever, 
            contextualize_q_prompt 
        )
        qa_system_prompt = """
        You are a movie recommendation system. Based on the provided context, recommend at least three movies that fit the user's needs. Your tone can be formal or conversational, adapting to the user's context. 
        Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know.Use three sentences maximum and keep the answer concise.

        Context: {context}

        Answer:
        Recommend at least one movie with their titles enclosed in double quotes, and provide brief descriptions for each without spoilers.
        """
     
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)

        self.rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        print("LLM and RetrievalQA chain initialized.")

    def chat(self, query):
        """Generate a response to the user's query using the LLM."""
        full_answer = ""  # Collect the complete response here
        for chunk in self.rag_chain.stream({"input": query, "chat_history": self.chat_history}):
            # Extract and yield only the 'answer' part of the chunk
            answer_part = chunk.get("answer", "")  # Use `.get()` to avoid KeyError
            full_answer += answer_part
            yield answer_part  # Yield only the 'answer' field

        # Update chat history with the full query and the full response
        self.chat_history.extend([
            HumanMessage(content=query),
            AIMessage(content=full_answer)
        ])
