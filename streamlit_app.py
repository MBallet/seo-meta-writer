import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from openai import OpenAI
import os

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_webpage_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    title = soup.title.string if soup.title else ""
    description = soup.find('meta', attrs={'name': 'description'})
    description = description['content'] if description else ""
    h1 = soup.h1.string if soup.h1 else ""
    body = ' '.join([p.text for p in soup.find_all('p')])[:500]
    
    return title, description, h1, body

def generate_meta(prompt, max_tokens):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant specialized in writing SEO-friendly metadata."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def main():
    st.title("Meta Writer")
    
    url = st.text_input("Enter URL:")
    target_keyword = st.text_input("Enter target keyword (optional):")
    
    if st.button("Generate Meta Data"):
        if url:
            current_title, current_description, h1, body = get_webpage_content(url)
            
            title_prompt = f"Write an SEO-friendly title for a webpage about '{h1}'. Current title: '{current_title}'. Target keyword: '{target_keyword}'. Body content: {body[:200]}..."
            description_prompt = f"Write an SEO-friendly meta description for a webpage about '{h1}'. Current description: '{current_description}'. Target keyword: '{target_keyword}'. Body content: {body[:200]}..."
            
            new_title = generate_meta(title_prompt, 60)
            new_description = generate_meta(description_prompt, 160)
            
            data = {
                "URL": [url],
                "Target Keyword": [target_keyword],
                "Current Title": [current_title],
                "Current Description": [current_description],
                "New Title": [new_title],
                "New Title Length": [len(new_title)],
                "New Description": [new_description],
                "New Description Length": [len(new_description)],
                "Body Copy": [body]
            }
            
            df = pd.DataFrame(data)
            st.dataframe(df)
        else:
            st.error("Please enter a valid URL.")

if __name__ == "__main__":
    main()