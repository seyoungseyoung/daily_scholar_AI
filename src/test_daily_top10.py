import arxiv
import datetime
from typing import List, Dict
import pandas as pd
import pytz
import time
import os
import schedule
from rank_papers import PaperQualityAnalyzer
from paper_analyzer import PaperAnalyzer
from analysis_manager import AnalysisManager
import json
from services.email_sender import EmailSender
import requests
import hashlib
import pickle

# Set timezone to KST
KST = pytz.timezone('Asia/Seoul')
os.environ['TZ'] = 'Asia/Seoul'
if hasattr(time, 'tzset'):
    time.tzset()

# Initialize analyzers
paper_analyzer = PaperAnalyzer()
analysis_manager = AnalysisManager()

def get_paper_hash(paper: Dict) -> str:
    """논문의 고유 해시값을 생성합니다."""
    paper_data = f"{paper['title']}{paper['url']}{paper['published']}"
    return hashlib.md5(paper_data.encode()).hexdigest()

def load_cached_analysis(paper_hash: str) -> Dict:
    """캐시된 분석 결과를 로드합니다."""
    cache_dir = "data/cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{paper_hash}.pkl")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"캐시 로드 중 오류 발생: {e}")
    return None

def save_cached_analysis(paper_hash: str, analysis_result: Dict):
    """분석 결과를 캐시에 저장합니다."""
    cache_dir = "data/cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{paper_hash}.pkl")
    
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(analysis_result, f)
    except Exception as e:
        print(f"캐시 저장 중 오류 발생: {e}")

def get_specific_date_papers(target_date: str) -> List[Dict]:
    try:
        # arxiv API 클라이언트 사용
        client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=3
        )
        
        # 단순한 검색 쿼리 사용 (cs.AI 카테고리만)
        query = 'cat:cs.AI'
        
        print(f"검색 쿼리: {query}")
        
        papers = []
        total_papers = 0
        max_results = 200  # 최대 200개까지 검색 (3일치면 충분)
        
        # 날짜 범위 계산
        target_start = datetime.datetime.strptime(target_date, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
        search_start = target_start - datetime.timedelta(days=1)  # 3일 전부터 검색
        search_end = target_start + datetime.timedelta(days=1)  # 다음 날까지
        
        print(f"검색 기간: {search_start.strftime('%Y-%m-%d')} ~ {search_end.strftime('%Y-%m-%d')}")
        
        # arxiv API 클라이언트 설정
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        # 논문 수집
        try:
            for paper in client.results(search):
                try:
                    # 게시일이 검색 범위를 벗어나면 중단
                    if paper.published < search_start:
                        print(f"\n검색 범위를 벗어난 논문 발견: {paper.published}")
                        break
                    
                    total_papers += 1
                    print(f"\n검색된 논문 ({total_papers}):")
                    print(f"제목: {paper.title}")
                    print(f"카테고리: {', '.join(paper.categories)}")
                    print(f"게시일: {paper.published} (UTC)")
                    print(f"업데이트일: {paper.updated} (UTC)")
                    
                    papers.append(paper)
                    print("-> 논문 추가")
                    
                    # 50개 단위로 진행 상황 출력
                    if total_papers % 50 == 0:
                        print(f"\n{total_papers}개 논문 처리 완료")
                        time.sleep(1)
                    
                except Exception as e:
                    print(f"논문 처리 중 오류 발생: {e}")
                    continue
                    
        except arxiv.UnexpectedEmptyPageError:
            print(f"\n총 {total_papers}개 논문 검색 완료")
        
        print(f"\n총 검색된 논문 수: {total_papers}")
        
        if not papers:
            print("논문이 발견되지 않았습니다.")
            return []
        
        # 대상 날짜의 논문만 필터링
        filtered_papers = []
        for paper in papers:
            if target_start <= paper.published < search_end:
                filtered_papers.append(paper)
        
        if filtered_papers:
            print(f"대상 기간 내 논문 수: {len(filtered_papers)}")
            return filtered_papers
        else:
            print("대상 기간 내 논문이 없습니다. 최신 논문 20개를 사용합니다.")
            return papers[:20]  # 최신 논문 20개 반환
        
    except Exception as e:
        print(f"논문 수집 중 오류 발생: {e}")
        print(f"오류 상세 정보: {str(e)}")
        import traceback
        print(f"스택 트레이스:\n{traceback.format_exc()}")
        return []

def save_top10(papers: List[Dict], analyzer: PaperQualityAnalyzer):
    # 논문 품질 점수 계산 및 정렬
    paper_scores = []
    for paper in papers:
        score = analyzer.analyze_paper(paper)
        paper_scores.append({
            'rank': 0,
            'title': paper.title.replace('\n', ' '),
            'url': paper.entry_id,
            'score': score,
            'authors': len(paper.authors),
            'categories': ', '.join(paper.categories),
            'published': paper.published.strftime('%Y-%m-%d'),
            'updated': paper.updated.strftime('%Y-%m-%d'),
            'abstract': paper.summary.replace('\n', ' ')
        })
    
    # 점수로 정렬
    paper_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # 상위 10개만 선택
    top10 = paper_scores[:1]
    
    # 순위 추가
    for i, paper in enumerate(top10, 1):
        paper['rank'] = i
    
    # DataFrame 생성
    df = pd.DataFrame(top10)
    
    # 결과 출력
    print(f"\n=== {datetime.datetime.now(pytz.UTC).strftime('%Y-%m-%d')}의 Top 10 논문 ===")
    print("순위 | 제목 | URL | 품질점수 | 저자수 | 카테고리 | 게시일 | 수정일")
    print("-" * 150)
    
    for _, paper in df.iterrows():
        title = paper['title'][:70] + '...' if len(paper['title']) > 70 else paper['title']
        print(f"{paper['rank']:2d} | {title} | {paper['url']} | {paper['score']:.2f} | {paper['authors']} | {paper['categories']} | {paper['published']} | {paper['updated']}")
    
    # CSV 파일로 저장
    os.makedirs('data/daily_top10', exist_ok=True)
    current_date = datetime.datetime.now(pytz.UTC).strftime('%Y%m%d')
    csv_file = f'data/daily_top10/top10_{current_date}.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"\nTop 10이 CSV 파일로 저장되었습니다: {csv_file}")
    
    return top10

def analyze_and_generate_report(papers: List[Dict], target_date: str):
    """논문을 분석하고 보고서를 생성합니다."""
    print("논문 분석 중...")
    
    # Create necessary directories
    os.makedirs("data/analysis", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    # Initialize analyzers
    analyzer = PaperQualityAnalyzer()
    
    # Get top 10 papers
    top10_papers = save_top10(papers, analyzer)
    
    # Analyze papers
    analysis_results = []
    for paper in top10_papers:
        print(f"\n논문 분석 시작: {paper['title']}")
        
        # 캐시 확인
        paper_hash = get_paper_hash(paper)
        cached_result = load_cached_analysis(paper_hash)
        
        if cached_result:
            print("캐시된 분석 결과를 사용합니다.")
            result = cached_result
        else:
            print("새로운 분석을 수행합니다.")
            result = paper_analyzer.analyze_paper(paper)
            # Add submission_date and html_url to result
            result['submission_date'] = paper['published']
            result['html_url'] = paper['url']
            # 캐시에 저장
            save_cached_analysis(paper_hash, result)
        
        analysis_results.append(result)
        print(f"분석 완료: {paper['title']}")
    
    # Save analysis results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    analysis_file = f"data/analysis/analysis_results_{timestamp}.json"
    
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n분석 결과가 저장되었습니다: {analysis_file}")
    
    # Generate HTML report
    print("\nHTML 보고서 생성 중...")
    report_file = analysis_manager.generate_report(analysis_results)
    print(f"HTML 보고서가 생성되었습니다: {report_file}")
    
    # Send email report
    print("\n이메일 발송 중...")
    email_sender = EmailSender()
    email_sender.send_report(analysis_results)
    
    return analysis_results

def run_daily_top10():
    try:
        # UTC 기준으로 현재 날짜에서 하루 전 계산
        utc = pytz.UTC
        now = datetime.datetime.now(utc)
        yesterday = now - datetime.timedelta(days=1)
        
        # 날짜를 UTC 자정으로 설정
        target_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        target_date_str = target_date.strftime('%Y-%m-%d')
        
        print(f"현재 시간 (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"대상 날짜 (UTC): {target_date_str}")
        print(f"{target_date_str}의 AI 논문을 가져오는 중...")
        
        papers = get_specific_date_papers(target_date_str)
        print(f"총 {len(papers)}개의 논문을 가져왔습니다.")
        
        if not papers:
            print("경고: 논문이 발견되지 않았습니다. 검색 기간을 확인해주세요.")
            return
        
        # 분석 및 보고서 생성
        analyze_and_generate_report(papers, target_date_str)
    except Exception as e:
        print(f"오류 발생: {e}")
        print(f"오류 상세 정보: {str(e)}")

def main():
    # 직접 실행
    print("Daily Scholar AI 테스트 실행을 시작합니다.")
    run_daily_top10()
    print("Daily Scholar AI 테스트 실행이 완료되었습니다.")

if __name__ == "__main__":
    main()  