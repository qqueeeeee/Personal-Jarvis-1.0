import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import os
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from typing import Optional
from googletrans import Translator
import yfinance as yf
from livekit.agents.llm import ChatMessage, ChatRole, ChatContent


@function_tool()
async def get_weather(
    context: RunContext,  
    city: str) -> str:
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather for {city}: {response.text.strip()}")
            return response.text.strip()   
        else:
            logging.error(f"Failed to get weather for {city}: {response.status_code}")
            return f"Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather for {city}: {e}")
        return f"An error occurred while retrieving weather for {city}." 

@function_tool()
async def search_web(
    context: RunContext,  
    query: str) -> str:
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        logging.info(f"Search results for '{query}': {results}")
        return results
    except Exception as e:
        logging.error(f"Error searching the web for '{query}': {e}")
        return f"An error occurred while searching the web for '{query}'."    

@function_tool()    
async def send_email(
    context: RunContext,  
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")  
        
        if not gmail_user or not gmail_password:
            logging.error("Gmail credentials not found in environment variables")
            return "Email sending failed: Gmail credentials not configured."
        
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        recipients = [to_email]
        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  
        server.login(gmail_user, gmail_password)
        
        text = msg.as_string()
        server.sendmail(gmail_user, recipients, text)
        server.quit()
        
        logging.info(f"Email sent successfully to {to_email}")
        return f"Email sent successfully to {to_email}"
        
    except smtplib.SMTPAuthenticationError:
        logging.error("Gmail authentication failed")
        return "Email sending failed: Authentication error. Please check your Gmail credentials."
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
        return f"Email sending failed: SMTP error - {str(e)}"
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return f"An error occurred while sending email: {str(e)}"


@function_tool()
async def translate_text(
    context: RunContext,  
    text: str,
    target_language: str) -> str:
    try:
        translator = Translator()
        translated = await translator.translate(text, dest=target_language)
        logging.info(f"Translated '{text}' to {target_language}: {translated.text}")
        return translated.text
    except Exception as e:
        logging.error(f"Error translating text: {e}")
        return f"An error occurred while translating text: {str(e)}"

@function_tool()
async def get_crypto_price(
    context: RunContext, 
    symbol: str) -> str:
    try:
        crypto = yf.Ticker(symbol + "-USD")
        data = crypto.history(period="1d")
        if not data.empty:
            price = round(data['Close'].iloc[-1], 2)
            logging.info(f"Crypto price for {symbol}: ${price}")
            return f"The current price of {symbol} is ${price}"
        else:
            logging.error(f"No data found for {symbol}")
            return f"No data found for {symbol}"
    except Exception as e:
        logging.error(f"Error fetching crypto price for {symbol}: {e}")
        return f"An error occurred while fetching crypto price: {str(e)}"

