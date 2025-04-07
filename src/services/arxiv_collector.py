import os
import time
import arxiv
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import pytz
from bs4 import BeautifulSoup
import re
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError

logger = logging.getLogger(__name__)

class ArxivCollector:
    def __init__(self):
        self.max_papers = 1000  # 최대 논문 수 증가
        self.target_categories = ['cs.AI']  # cs.AI만 검색
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.papers_dir = os.path.join(self.base_dir, 'data', 'papers')
        self.html_dir = os.path.join(self.base_dir, 'data', 'html')
        self.text_dir = os.path.join(self.base_dir, 'data', 'text')
        os.makedirs(self.papers_dir, exist_ok=True)
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.text_dir, exist_ok=True)

    def download_pdf(self, url: str, filename: str) -> bool:
        """PDF 파일 다운로드"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            filepath = os.path.join(self.papers_dir, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            logger.error(f"PDF 다운로드 중 오류 발생: {str(e)}")
            return False

    def download_html(self, entry_id: str) -> bool:
        """HTML 버전 논문 다운로드 및 저장"""
        try:
            # HTML URL 생성 (experimental 버전)
            paper_id = entry_id.split('/')[-1]
            html_url = f"https://arxiv.org/html/{paper_id}"
            
            # HTML 다운로드
            response = requests.get(html_url)
            response.raise_for_status()
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 메타데이터 제거
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # 본문 추출
            main_content = soup.find('main')
            if not main_content:
                logger.error(f"본문을 찾을 수 없음: {html_url}")
                return False
            
            # 이미지 URL 수정
            for img in main_content.find_all('img'):
                if img.get('src', '').startswith('/'):
                    img['src'] = f"https://arxiv.org{img['src']}"
            
            # 파일명 생성
            filename = f"{paper_id}.html"
            
            # HTML 저장
            filepath = os.path.join(self.html_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(main_content))
            
            return True
        except Exception as e:
            logger.error(f"HTML 다운로드 중 오류 발생: {str(e)}")
            return False

    def extract_text_from_pdf(self, pdf_path: str, output_path: str) -> bool:
        """PDF에서 텍스트 추출"""
        try:
            text = extract_text(pdf_path)
            
            # 텍스트 정리
            text = re.sub(r'\s+', ' ', text)  # 연속된 공백 제거
            text = text.strip()
            
            # 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            return True
        except (PDFSyntaxError, Exception) as e:
            logger.error(f"PDF 텍스트 추출 중 오류 발생: {str(e)}")
            return False

    def collect(self) -> List[Dict[str, Any]]:
        """논문 정보 수집"""
        try:
            # 검색 쿼리 생성
            query = 'cat:cs.AI'
            
            # arxiv API 클라이언트 설정
            client = arxiv.Client(
                page_size=100,  # 한 번에 가져올 결과 수
                delay_seconds=3.0,  # 요청 간 지연 시간
                num_retries=3  # 실패 시 재시도 횟수
            )
            
            search = arxiv.Search(
                query=query,
                max_results=self.max_papers,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            papers = []
            one_day_ago = datetime.now(pytz.UTC) - timedelta(days=1)

            # 논문 수집
            for result in client.results(search):
                # 최근 1일 이내의 논문만 수집
                if result.published < one_day_ago:
                    continue

                # PDF 다운로드 및 텍스트 추출
                paper_id = result.entry_id.split('/')[-1]
                pdf_filename = f"{paper_id}.pdf"
                pdf_path = os.path.join(self.papers_dir, pdf_filename)
                text_path = os.path.join(self.text_dir, f"{paper_id}.txt")
                
                if self.download_pdf(result.pdf_url, pdf_filename):
                    self.extract_text_from_pdf(pdf_path, text_path)

                # HTML 다운로드 시도
                html_success = self.download_html(result.entry_id)

                # 논문 정보 저장
                paper_info = {
                    "title": result.title,
                    "authors": ', '.join([author.name for author in result.authors]),
                    "abstract": result.summary,
                    "submission_date": result.published,
                    "categories": result.categories,
                    "pdf_url": result.pdf_url,
                    "html_url": result.entry_id,
                    "pdf_path": pdf_path,
                    "text_path": text_path,
                    "html_success": html_success
                }
                papers.append(paper_info)
                logger.info(f"논문 수집 완료: {result.title}")

            return papers

        except Exception as e:
            logger.error(f"논문 수집 중 오류 발생: {str(e)}")
            return [] 