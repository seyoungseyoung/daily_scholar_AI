import json
import requests
from typing import Dict, Any, List
import time
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, ANALYSIS_PROMPTS

class PaperAnalyzer:
    def __init__(self):
        if not DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY 환경 변수가 설정되지 않았습니다.")
            
        self.headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def _call_api(self, prompt: str, model: str = "deepseek-chat") -> str:
        """DeepSeek API를 호출하여 응답을 받아옵니다."""
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a helpful AI assistant that analyzes academic papers.
When analyzing papers:
1. For classification, provide one main field and 5-8 tags
2. For summary, structure the content clearly with sections
3. For translation, maintain academic tone while being clear
Always format your response according to the specified format in the prompt."""
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"API 호출 중 오류 발생: {str(e)}")
            raise
    
    def _parse_classification(self, response: str) -> Dict[str, Any]:
        """분류 응답을 파싱합니다."""
        lines = response.strip().split('\n')
        classification = ""
        tags = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('분류:'):
                # 분류 추출 및 정리
                classification = line.replace('분류:', '').strip()
                classification = classification.strip('[]').strip()
            elif line.startswith('태그:'):
                # 태그 추출 및 정리
                tags_text = line.replace('태그:', '').strip()
                # 쉼표로 분리하고 대괄호와 공백 제거
                tags = [
                    tag.strip().strip('[]').strip()
                    for tag in tags_text.split(',')
                    if tag.strip() and not tag.isspace()
                ]
                # 빈 태그 제거
                tags = [tag for tag in tags if tag]
        
        # 태그가 없거나 3개 미만이면 기본 태그 생성
        if not tags or len(tags) < 3:
            if '컴퓨터 비전' in classification:
                tags = ['Computer Vision', 'Object Detection', 'Deep Learning', 'Image Processing', 'Neural Networks']
            elif '인공지능' in classification or '강화학습' in classification:
                tags = ['Artificial Intelligence', 'Machine Learning', 'Neural Networks', 'Reinforcement Learning', 'Deep Learning']
            elif '수중' in classification or 'Underwater' in classification:
                tags = ['Underwater Vision', 'Object Detection', 'Spiking Neural Networks', 'Energy Efficiency', 'Computer Vision']
        
        # 백엔드 관련 태그 제거
        tags = [tag for tag in tags if not any(x in tag.lower() for x in ['backend', 'api', 'server', 'database'])]
        
        return {
            "classification": classification,
            "tags": tags
        }
    
    def _clean_response(self, text: str) -> str:
        """응답을 HTML 형식으로 변환하고 정리합니다."""
        # 잘못된 blockquote 태그 제거
        text = text.replace('</blockquote>', '')
        text = text.replace('<blockquote>', '')
        
        # 마크다운 헤더를 HTML 헤더로 변환 (최소화)
        text = text.replace('### ', '<h3>')
        text = text.replace('## ', '<h2>')
        text = text.replace('# ', '<h2>')  # h1은 제목에만 사용
        
        # 헤더 닫기 태그 추가
        text = text.replace('\n', '</h3>\n', 1) if '<h3>' in text else text
        text = text.replace('\n', '</h2>\n', 1) if '<h2>' in text else text
        
        # 볼드 처리 개선
        text = text.replace('**', '<strong>')
        text = text.replace('**', '</strong>', 1)
        
        # 구분선을 HTML 구분선으로 변환
        text = text.replace('---\n', '<hr>\n')
        
        # 줄바꿈 정리 및 단락 처리
        lines = text.split('\n')
        cleaned_lines = []
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_paragraph:
                    cleaned_lines.append('<p>' + ' '.join(current_paragraph) + '</p>')
                    current_paragraph = []
            else:
                # 불필요한 공백 제거
                line = ' '.join(line.split())
                current_paragraph.append(line)
        
        if current_paragraph:
            cleaned_lines.append('<p>' + ' '.join(current_paragraph) + '</p>')
        
        # 연속된 빈 줄 제거
        result = '\n'.join(cleaned_lines)
        result = result.replace('\n\n\n', '\n\n')
        result = result.replace('\n\n\n', '\n\n')
        
        return result
    
    def _translate_abstract(self, abstract: str) -> str:
        """초록을 한국어로 번역합니다."""
        print("한국어 번역 중...")
        
        prompt = f"""다음은 논문 초록을 한국어로 번역하는 요구사항입니다:

1. 번역 대상: 다음 영문 초록을 한국어로 번역해주세요.
2. 번역 규칙:
   - 모든 전문 용어는 원문(영어)을 병기하고 <strong>태그로 강조 표시합니다. (예: 분리 배치 정규화(<strong>Separated Batch Normalization, SeBN</strong>))
   - 의미 단위로 개행해 가독성을 높입니다.
   - '-입니다' 체계를 유지하며 자연스러운 전문성을 확보합니다.
   - 모델명, 기술, 성능 지표 등은 <strong>태그로 굵게 표시해 시각적 강조를 적용합니다.

영문 초록:
{abstract}

한국어 번역:"""
        
        response = self._call_api(prompt, model="deepseek-chat")
        
        # 번역 규칙 부분 제거
        if "번역 규칙" in response:
            response = response.split("번역 규칙")[0].strip()
            
        # '---' 이후의 내용 제거
        if "---" in response:
            response = response.split("---")[0].strip()
            
        # '번역 특징' 부분 제거
        if "번역 특징" in response:
            response = response.split("번역 특징")[0].strip()
        
        print("번역 완료")
        return response

    def _analyze_paper_content(self, title: str, abstract: str) -> Dict[str, Any]:
        """논문 내용을 분석합니다."""
        # 분류 및 태그 생성
        classification_response = self._call_api(
            ANALYSIS_PROMPTS["classification"].format(
                title=title,
                abstract=abstract
            ),
            model="deepseek-reasoner"
        )
        classification_result = self._parse_classification(classification_response)
        
        # 요약 생성
        summary_response = self._call_api(
            ANALYSIS_PROMPTS["summary"].format(
                title=title,
                abstract=abstract
            ),
            model="deepseek-reasoner"
        )
        summary = self._clean_response(summary_response)
        
        return {
            "classification": classification_result["classification"],
            "tags": list(set(classification_result["tags"])),
            "summary": summary
        }
    
    def analyze_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """논문을 분석하고 결과를 반환합니다."""
        print(f"\n논문 분석 시작: {paper['title']}")
        
        # 번역 생성
        print("한국어 번역 중...")
        translation = self._translate_abstract(paper["abstract"])
        print("번역 완료")
        
        # 논문 내용 분석
        print("논문 내용 분석 중...")
        analysis_result = self._analyze_paper_content(paper["title"], paper["abstract"])
        print("분석 완료")
        
        # 결과 반환
        result = {
            "paper_id": paper["url"],
            "title": paper["title"],
            **analysis_result,
            "translation": translation,
            "original_abstract": paper["abstract"]
        }
        
        print(f"논문 분석 완료: {paper['title']}")
        return result
    
    def analyze_papers(self, papers: list) -> list:
        """여러 논문을 분석합니다."""
        results = []
        for paper in papers:
            result = self.analyze_paper(paper)
            results.append(result)
        return results 