import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from openai import OpenAI
import os
import io
import csv

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_webpage_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.title.string if soup.title else ""
        description = soup.find('meta', attrs={'name': 'description'})
        description = description['content'] if description else ""
        h1 = soup.h1.string if soup.h1 else ""
        body = ' '.join([p.text for p in soup.find_all('p')])[:500]
        
        return title, description, h1, body
    except Exception as e:
        st.error(f"Error fetching {url}: {str(e)}")
        return "", "", "", ""

def generate_meta(prompt, max_tokens):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialized in writing SEO-friendly metadata."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating meta: {str(e)}")
        return ""

def process_url(url, target_keyword):
    current_title, current_description, h1, body = get_webpage_content(url)
    
    title_prompt = f"Write an SEO-friendly title for a webpage about '{h1}'. Current title: '{current_title}'. Target keyword: '{target_keyword}'. Body content: {body[:200]}..."
    description_prompt = f"Write an SEO-friendly meta description for a webpage about '{h1}'. Current description: '{current_description}'. Target keyword: '{target_keyword}'. Body content: {body[:200]}..."
    
    new_title = generate_meta(title_prompt, 60)
    new_description = generate_meta(description_prompt, 160)
    
    return {
        "URL": url,
        "Target Keyword": target_keyword,
        "Current Title": current_title,
        "Current Description": current_description,
        "New Title": new_title,
        "New Title Length": len(new_title),
        "New Description": new_description,
        "New Description Length": len(new_description),
        "Body Copy": body
    }

def main():
    st.title("Meta Writer")
    
    input_method = st.radio("Choose input method:", ["Single URL", "Multiple URLs (Paste)", "Upload CSV"])
    
    if input_method == "Single URL":
        url = st.text_input("Enter URL:")
        target_keyword = st.text_input("Enter target keyword (optional):")
        urls = [(url, target_keyword)] if url else []
    
    elif input_method == "Multiple URLs (Paste)":
        url_list = st.text_area("Paste URLs (one per line, optionally followed by a comma and target keyword):")
        urls = [line.strip().split(',') for line in url_list.split('\n') if line.strip()]
        urls = [(url.strip(), keyword.strip() if len(parts) > 1 else "") for parts in urls for url, *keyword in [parts]]
    
    else:  # Upload CSV
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            content = uploaded_file.getvalue().decode('utf-8')
            csv_reader = csv.reader(io.StringIO(content))
            urls = [(row[0].strip(), row[1].strip() if len(row) > 1 else "") for row in csv_reader]

    if st.button("Generate Meta Data"):
        if urls:
            results = []
            progress_bar = st.progress(0)
            for i, (url, keyword) in enumerate(urls):
                result = process_url(url, keyword)
                results.append(result)
                progress_bar.progress((i + 1) / len(urls))
            
            df = pd.DataFrame(results)
            st.dataframe(df)
            
            # Offer CSV download
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download results as CSV",
                data=csv,
                file_name="meta_writer_results.csv",
                mime="text/csv",
            )
        else:
            st.error("Please enter at least one valid URL.")

if __name__ == "__main__":
    main()