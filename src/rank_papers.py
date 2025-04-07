import arxiv
import datetime
from typing import List, Dict
import pandas as pd
import pytz
import time
import os

class PaperQualityAnalyzer:
    def __init__(self):
        self.quality_indicators = {
            'author_metrics': 0.3,    # 저자 관련 지표
            'paper_metrics': 0.3,     # 논문 특성 지표
            'time_metrics': 0.2,      # 시간 관련 지표
            'content_metrics': 0.2    # 내용 관련 지표
        }
    
    def analyze_paper(self, paper: Dict) -> float:
        """논문의 품질 점수를 계산합니다."""
        try:
            score = 0.0
            
            # 제목 분석
            title = paper.get('title', '')
            if len(title) > 0:
                score += 0.2
            
            # 저자 수 분석
            authors = paper.get('authors', [])
            if len(authors) >= 2:
                score += 0.2
            
            # 카테고리 분석
            categories = paper.get('categories', [])
            if len(categories) >= 1:
                score += 0.2
            
            # 초록 분석
            abstract = paper.get('abstract', '')
            if len(abstract) > 100:
                score += 0.4
            
            return min(score, 1.0)
            
        except Exception as e:
            print(f"논문 품질 분석 중 오류 발생: {e}")
            return 0.0
    
    def _calculate_author_score(self, paper) -> float:
        score = 0
        # 저자 수 평가 (1-5명이 최적)
        author_count = len(paper.authors)
        if 1 <= author_count <= 3:
            score += 1.0
        elif 4 <= author_count <= 5:
            score += 0.8
        elif 6 <= author_count <= 8:
            score += 0.5
        else:
            score += 0.3
            
        # 저자 정보 완성도
        if all(hasattr(author, 'name') for author in paper.authors):
            score += 0.5
        elif any(hasattr(author, 'name') for author in paper.authors):
            score += 0.3
            
        return score
    
    def _calculate_paper_score(self, paper) -> float:
        score = 0
        # 제목 품질 평가
        title_words = paper.title.split()
        title_length = len(title_words)
        if 5 <= title_length <= 10:
            score += 0.8
        elif 11 <= title_length <= 15:
            score += 0.6
        else:
            score += 0.4
            
        # 제목의 명확성 (특수문자, 대문자 사용 등)
        if any(word[0].isupper() for word in title_words):
            score += 0.2
            
        # 초록 품질 평가
        abstract_words = paper.summary.split()
        abstract_length = len(abstract_words)
        if abstract_length >= 200:
            score += 0.8
        elif abstract_length >= 100:
            score += 0.6
        else:
            score += 0.4
            
        # 카테고리 다양성
        category_count = len(paper.categories)
        if category_count >= 3:
            score += 0.5
        elif category_count == 2:
            score += 0.3
        else:
            score += 0.1
            
        return score
    
    def _calculate_time_score(self, paper) -> float:
        score = 0
        current_time = datetime.datetime.now(pytz.UTC)
        
        # 최근성 평가
        time_diff = current_time - paper.updated
        if time_diff.days <= 1:
            score += 0.5
        elif time_diff.days <= 3:
            score += 0.4
        elif time_diff.days <= 5:
            score += 0.3
        else:
            score += 0.2
            
        # 버전 관리 평가
        if paper.published != paper.updated:
            update_diff = paper.updated - paper.published
            if update_diff.days <= 3:
                score += 0.5
            else:
                score += 0.3
                
        return score
    
    def _calculate_content_score(self, paper) -> float:
        score = 0
        abstract = paper.summary.lower()
        
        # 방법론 언급 평가
        method_keywords = ['method', 'approach', 'algorithm', 'technique', 'framework', 'model', 'architecture']
        method_count = sum(1 for keyword in method_keywords if keyword in abstract)
        score += min(method_count * 0.2, 0.6)  # 최대 0.6점
        
        # 실험/평가 언급 평가
        eval_keywords = ['experiment', 'evaluation', 'result', 'performance', 'benchmark', 'comparison']
        eval_count = sum(1 for keyword in eval_keywords if keyword in abstract)
        score += min(eval_count * 0.2, 0.4)  # 최대 0.4점
        
        return score

def get_recent_papers(days: int = 7) -> List[Dict]:
    # 7일 전 날짜 계산 (UTC 기준)
    end_date = datetime.datetime.now(pytz.UTC)
    start_date = end_date - datetime.timedelta(days=days)
    
    # arXiv 검색 쿼리 생성
    client = arxiv.Client()
    search = arxiv.Search(
        query='cat:cs.AI',
        max_results=100,  # 한 번에 가져올 최대 결과 수 제한
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    # 논문 수집
    papers = []
    try:
        for paper in client.results(search):
            if paper.published < start_date:
                break
            papers.append(paper)
            time.sleep(0.1)  # API 요청 간 간격 추가
    except Exception as e:
        print(f"논문 수집 중 오류 발생: {e}")
        if not papers:  # 논문을 하나도 수집하지 못한 경우
            raise
    
    return papers

def main():
    # 논문 품질 분석기 초기화
    analyzer = PaperQualityAnalyzer()
    
    # 최근 7일간의 논문 가져오기
    print("최근 7일간의 cs.AI 논문을 가져오는 중...")
    papers = get_recent_papers()
    print(f"총 {len(papers)}개의 논문을 가져왔습니다.")
    
    # 논문 품질 점수 계산 및 정렬
    print("논문 품질 점수를 계산하는 중...")
    paper_scores = []
    for paper in papers:
        score = analyzer.analyze_paper(paper)
        paper_scores.append({
            'rank': 0,  # 순위는 나중에 추가
            'title': paper.title.replace('\n', ' '),  # 제목에서 줄바꿈 제거
            'url': paper.entry_id,  # arXiv 링크
            'score': score,
            'authors': len(paper.authors),
            'categories': ', '.join(paper.categories),  # 카테고리 추가
            'published': paper.published.strftime('%Y-%m-%d'),  # 날짜 형식 지정
            'updated': paper.updated.strftime('%Y-%m-%d'),  # 업데이트 날짜 추가
            'abstract': paper.summary.replace('\n', ' ')  # 초록 추가
        })
    
    # 점수로 정렬
    paper_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # 순위 추가
    for i, paper in enumerate(paper_scores, 1):
        paper['rank'] = i
    
    # DataFrame 생성
    df = pd.DataFrame(paper_scores)
    
    # 결과 출력
    print("\n=== 최근 7일간의 cs.AI 논문 순위 ===")
    print("순위 | 제목 | URL | 품질점수 | 저자수 | 카테고리 | 게시일 | 수정일")
    print("-" * 150)
    
    for _, paper in df.iterrows():
        title = paper['title'][:70] + '...' if len(paper['title']) > 70 else paper['title']
        print(f"{paper['rank']:2d} | {title} | {paper['url']} | {paper['score']:.2f} | {paper['authors']} | {paper['categories']} | {paper['published']} | {paper['updated']}")
    
    # CSV 파일로 저장
    os.makedirs('data/rankings', exist_ok=True)
    current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = f'data/rankings/paper_rankings_{current_time}.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"\n순위가 CSV 파일로 저장되었습니다: {csv_file}")

if __name__ == "__main__":
    main() 