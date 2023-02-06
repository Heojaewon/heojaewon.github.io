import re
import zipfile
import openai
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, timedelta

def generate_text(prompt):
    # 모델 엔진 선택
    model_engine = "text-davinci-003"

    # 맥스 토큰
    max_tokens = 3500

    # 블로그 생성
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.3,      # creativity
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return completion

def extract_tags(body):
    hashtag_pattern = r'(#+[a-zA-Z0-9(_)]{1,})'
    hashtags = [w[1:] for w in re.findall(hashtag_pattern, body)]
    hashtags = list(set(hashtags))
    tag_string = ""
    for w in hashtags:
        # 3글자 이상 추출
        if len(w) > 3:
            tag_string += f'{w}, '
    tag_string = re.sub(r'[^a-zA-Z, ]', '', tag_string)
    tag_string = tag_string.strip()[:-1]
    return tag_string

def get_file(filename):
    with open(filename, 'r') as f:
        data = f.read()
    return data

def make_prompt(prompt, topic='<<TOPIC>>', category='<<CATEGORY>>'):
    if topic:
        prompt = prompt.replace('<<TOPIC>>', topic)
    if category:
        prompt = prompt.replace('<<CATEGORY>>', category)
    return prompt

def make_header(topic, category, tags):
    # 블로그 헤더
    page_head = f'''---
layout: single
title:  "{topic}"
categories: {category}
tag: [{tags}]
toc: false
author_profile: false
---'''
    return page_head

prompt_example = f'''Write blog posts in markdown format.
Write the theme of your blog as "<<TOPIC>>" and its category is "<<CATEGORY>>".
Highlight, bold, or italicize important words or sentences.
Please include the restaurant's address, menu recommendations and other helpful information(opening and closing hours) as a list style.
Please make the entire blog less than 10 minutes long.
The audience of this article is 20-40 years old.
Create several hashtags and add them only at the end of the line.
Add a summary of the entire article at the beginning of the blog post.'''

with st.sidebar:
#     st.markdown('''
# **API KEY 발급 방법**
# 1. https://beta.openai.com/ 회원가입
# 2. https://beta.openai.com/account/api-keys 접속
# 3. `create new secret key` 클릭 후 생성된 KEY 복사
#     ''')
    st.write("# Hello! 👋")

    components.html(
        '''
        <img src="https://i0.wp.com/www.ifthen.ai/wp-content/uploads/2019/02/20561EC6-9ABF-4818-A035-FD1B583079F4.png" width="200px">
        '''
    )

    st.header('OPEN AI')

    value=''
    apikey = st.text_input(label='OPENAI API KEY', placeholder='OPENAI API KEY를 입력해 주세요', value=value)

    if apikey:
        st.markdown(f'OPENAI API KEY: `{apikey}`')

    st.markdown('---')

# Preset Container
preset_container = st.container()
preset_container.subheader('1. 설정')
tab_single, tab_multiple = preset_container.tabs(['1개 생성', '여러개 생성'])

col1, co12 =  tab_single.columns(2)

topic = col1.text_input(label='주제 입력', placeholder='주제를 입력해 주세요')
col1.markdown('(예시)')
col1.markdown('`Top 10 Restaurants you must visit when traveling to New York`')

category = co12.text_input(label='카테고리 입력', placeholder='카테고리를 입력해 주세요')
co12.markdown('(예시)')
co12.markdown('`Travel`')

def generate_blog(apikey, topic, category, prompt):
    # apikey 셋팅
    openai.api_key = apikey
    # prompt 생성
    prompt_output = make_prompt(prompt=prompt, topic=topic, category=category)
    # 글 생성
    response = generate_text(prompt_output)
    body = response.choices[0].text
    # 태그 생성
    tags = extract_tags(body)

    # header 생성
    header = make_header(topic=topic, category=category, tags=tags)
    # 첫 줄은 타이틀(제목)과 겹치기 때문에 제거하도록 합니다.
    body = '\n'.join(response['choices'][0]['text'].strip().split('\n')[1:])
    # 최종 결과물
    output = header + body

    yesterday = datetime.now() - timedelta(days=1)
    timestring = yesterday.strftime('%Y-%m-%d')
    filename = f"{timestring}-{'-'.join(topic.lower().split())}.txt"
    # filename = f"{timestring}-{'-'.join(topic.lower().split())}.md"
    with open(filename, 'w') as f:
        f.write(output)
        f.close()
    return filename

with tab_single:
    # Prompt Container
    prompt_container = st.container()
    prompt_container.markdown('''\n''')
    prompt_container.subheader('2. 작성 글')
    prompt_container.markdown('[tip 1] [구글 번역기] (https://translate.google.com/)')
    prompt_container.markdown('[tip 2] `<<TOPIC>>`은 입력한 주제로 `<<CATEGORY>>`는 입력한 카테고리로 **치환**.')
    # prompt_container.markdown('(예시)')
    # 예시 필드 prompt_container.markdown(f'''
    # ```
    # {prompt_example}''')

    prompt = prompt_container.text_area(label='입력',
                                        placeholder='입력해 주세요',
                                        key='prompt1',
                                        height=250)

    # 미리보기 출력
    if prompt:
        prompt_output = make_prompt(prompt=prompt, topic=topic, category=category)

        prompt_container.markdown(f'```{prompt_output}')

    # 블로그 생성
    if apikey and topic and category and prompt:
        button = prompt_container.button('생성하기')

        if button:
            filename = generate_blog(apikey=apikey, topic=topic, category=category, prompt=prompt)
            download_btn = prompt_container.download_button(label='파일 다운로드', 
                                                data=get_file(filename=filename),
                                                file_name=filename,
                                                mime='text/markdown')

with tab_multiple:
    file_upload = st.file_uploader("파일 선택(csv)", type=['csv'])
    if file_upload:
        df = pd.read_csv(file_upload)
        df['topic'] = df.apply(lambda x: x['topic'].replace('<<KEYWORD>>', x['keyword']), axis=1)
        st.dataframe(df)

        # Prompt Container
        prompt_container2 = st.container()
        prompt_container2.subheader('2. 세부지침')
        prompt_container2.markdown('[tip 1] **세부지침**은 [구글 번역기](https://translate.google.com/)로 돌려서 **영어로** 입력해 주세요')
        prompt_container2.markdown('[tip 2] `<<TOPIC>>`은 입력한 주제로 `<<CATEGORY>>`는 입력한 카테고리로 **치환**됩니다.')
        prompt_container2.markdown('(예시)')
        prompt_container2.markdown(f'''
        ```
        {prompt_example}''')

        prompt2 = prompt_container2.text_area(label='세부지침 입력', 
                                              placeholder='지침을 입력해 주세요',  
                                              key='prompt2',
                                              height=250)

        total = len(df)
        button2 = prompt_container2.button(f'{total}개 파일 생성하기')

        if button2:
            generate_progress = st.progress(0)            
            st.write(f"[알림] 총{total} 개의 블로그를 생성합니다!")
            blog_files = []
            for i, row in df.iterrows():
                filename = generate_blog(apikey=apikey, topic=row['topic'], category=row['category'], prompt=prompt2)
                blog_files.append(filename)
                st.write(f"[완료] {row['topic']}")
                generate_progress.progress((i + 1) / total)

            yesterday = datetime.now() - timedelta(days=1)
            timestring = yesterday.strftime('%Y-%m-%d')
            zip_filename = f'{timestring}-files.zip'
            with zipfile.ZipFile(zip_filename, 'w') as myzip:
                for f in blog_files:
                    myzip.write(f)
                myzip.close()

            with open(zip_filename, "rb") as fzip:
                download_btn2 = st.download_button(label="파일 다운로드",
                                                   data=fzip,
                                                   file_name=zip_filename,
                                                   mime="application/zip"
    )


