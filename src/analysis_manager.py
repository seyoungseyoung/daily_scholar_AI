import json
import os
from datetime import datetime
from typing import List, Dict, Any
from paper_analyzer import PaperAnalyzer

class AnalysisManager:
    def __init__(self):
        self.analyzer = PaperAnalyzer()
        self.results_dir = "data/analysis"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def load_papers(self, csv_path: str) -> List[Dict[str, Any]]:
        """CSV 파일에서 논문 데이터를 로드합니다."""
        import pandas as pd
        df = pd.read_csv(csv_path)
        return df.to_dict('records')
    
    def save_analysis(self, results: List[Dict[str, Any]]):
        """분석 결과를 JSON 파일로 저장합니다."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.results_dir, f"analysis_{timestamp}.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"분석 결과가 저장되었습니다: {output_path}")
    
    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """분석 결과를 HTML 보고서로 생성합니다."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # CSS 스타일
        css = """
            :root {
                --primary-color: #2196f3;
                --secondary-color: #4caf50;
                --background-color: #f8f9fa;
                --text-color: #2c3e50;
                --border-color: #e0e0e0;
                --tag-bg: #e1f5fe;
                --tag-hover: #b3e5fc;
            }
            
            body { 
                font-family: 'Noto Sans KR', Arial, sans-serif; 
                margin: 0;
                padding: 20px;
                background-color: var(--background-color);
                color: var(--text-color);
                line-height: 1.6;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
                padding: 30px;
                background: linear-gradient(135deg, #2196f3, #1976d2);
                color: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(33, 150, 243, 0.2);
            }
            
            .header h1 {
                margin: 0;
                font-size: 2.2em;
                font-weight: 700;
            }
            
            .header p {
                margin: 10px 0 0;
                opacity: 0.9;
            }
            
            .paper {
                margin-bottom: 40px;
                padding: 30px;
                border: 1px solid var(--border-color);
                border-radius: 16px;
                background: white;
                transition: all 0.3s ease;
            }
            
            .paper:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            }
            
            .title {
                font-size: 1.6em;
                font-weight: 700;
                color: var(--text-color);
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid var(--border-color);
                line-height: 1.4;
            }
            
            .section {
                margin: 25px 0;
            }
            
            .section h3 {
                color: var(--primary-color);
                font-size: 1.3em;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid var(--border-color);
                display: flex;
                align-items: center;
            }
            
            .section h3::before {
                content: "•";
                color: var(--primary-color);
                font-size: 1.5em;
                margin-right: 10px;
            }
            
            .tags {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin: 15px 0;
            }
            
            .tag {
                background: var(--tag-bg);
                padding: 8px 16px;
                border-radius: 25px;
                font-size: 0.95em;
                color: var(--primary-color);
                transition: all 0.2s ease;
                cursor: pointer;
                border: 1px solid rgba(33, 150, 243, 0.2);
            }
            
            .tag:hover {
                background: var(--tag-hover);
                transform: translateY(-2px);
                box-shadow: 0 2px 4px rgba(33, 150, 243, 0.2);
            }
            
            .classification {
                color: var(--primary-color);
                font-weight: 600;
                font-size: 1.2em;
                margin: 15px 0;
                padding: 10px 15px;
                background: var(--tag-bg);
                border-radius: 8px;
                display: inline-block;
            }
            
            .summary-section, .translation-section {
                background: var(--background-color);
                padding: 25px;
                border-radius: 12px;
                margin: 20px 0;
                position: relative;
            }
            
            .summary-section {
                border-left: 4px solid var(--primary-color);
            }
            
            .translation-section {
                border-left: 4px solid var(--secondary-color);
            }
            
            .highlight {
                background: #fff3e0;
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: 600;
                color: #e65100;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
                padding: 20px;
                background: linear-gradient(135deg, #e3f2fd, #bbdefb);
                border-radius: 12px;
            }
            
            .stat-item {
                text-align: center;
                padding: 15px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                transition: transform 0.2s ease;
            }
            
            .stat-item:hover {
                transform: translateY(-2px);
            }
            
            .stat-label {
                font-size: 0.95em;
                color: #666;
                margin-bottom: 8px;
            }
            
            .stat-value {
                font-size: 1.4em;
                font-weight: 700;
                color: var(--primary-color);
            }
            
            .paper-meta {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid var(--border-color);
                font-size: 0.9em;
                color: #666;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 15px;
                }
                
                .paper {
                    padding: 20px;
                }
                
                .header {
                    padding: 20px;
                }
                
                .header h1 {
                    font-size: 1.8em;
                }
                
                .stats {
                    grid-template-columns: 1fr;
                }
            }
        """
        
        # HTML 시작
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "<title>AI 논문 분석 보고서</title>",
            "<link href='https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap' rel='stylesheet'>",
            f"<style>{css}</style>",
            "</head>",
            "<body>",
            "<div class='container'>",
            "<div class='header'>",
            "<h1>AI 논문 분석 보고서</h1>",
            f"<p>생성일: {timestamp}</p>",
            "</div>"
        ]
        
        # 논문 섹션 생성
        for paper in results:
            # 성능 통계 추출
            stats = []
            if "78.8%" in paper['summary']:
                stats.append(("정확도", "78.8%"))
            if "6.97M" in paper['summary']:
                stats.append(("모델 크기", "6.97M"))
            if "2.98mJ" in paper['summary']:
                stats.append(("에너지 소모", "2.98mJ"))
            
            paper_html = [
                "<div class='paper'>",
                f"<div class='title'>{paper['title']}</div>",
                "<div class='section'>",
                "<h3>분류 및 태그</h3>",
                f"<div class='classification'>분류: {paper['classification']}</div>",
                "<div class='tags'>",
                "".join([f"<span class='tag'>{tag}</span>" for tag in paper['tags']]),
                "</div>",
                "</div>"
            ]
            
            # 성능 통계 섹션 추가
            if stats:
                paper_html.extend([
                    "<div class='section'>",
                    "<h3>주요 성능 지표</h3>",
                    "<div class='stats'>",
                    "".join([
                        f"<div class='stat-item'><div class='stat-label'>{label}</div><div class='stat-value'>{value}</div></div>"
                        for label, value in stats
                    ]),
                    "</div>",
                    "</div>"
                ])
            
            paper_html.extend([
                "<div class='section'>",
                "<h3>논문 설명</h3>",
                "<div class='summary-section'>",
                paper['summary'].replace('\n', '</p><p>'),
                "</div>",
                "</div>",
                "<div class='section'>",
                "<h3>한국어 번역</h3>",
                "<div class='translation-section'>",
                paper['translation'] if isinstance(paper['translation'], str) else paper['translation'].get('abstract', ''),
                "</div>",
                "</div>",
                "<div class='paper-actions'>",
                f"<a href='https://arxiv.org/abs/{paper['paper_id']}' target='_blank' class='paper-link'>논문 보기</a>",
                "</div>",
                "<div class='paper-meta'>",
                f"<div class='tags'>",
                "".join([f"<span class='tag'>{tag}</span>" for tag in paper['tags']]),
                "</div>",
                f"<div class='paper-date'>{paper['submission_date']}</div>",
                "</div>",
                "</div>"
            ])
            html.extend(paper_html)
        
        # HTML 닫기
        html.extend(["</div>", "</body>", "</html>"])
        
        # HTML 문자열 생성
        html_content = "\n".join(html)
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.results_dir, f"report_{timestamp}.html")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"보고서가 생성되었습니다: {report_path}")
        return report_path
    
    def process_papers(self, analysis_results):
        """분석 결과를 처리하고 HTML 보고서를 생성합니다."""
        print("HTML 보고서 생성 중...")
        
        # HTML 파일 생성
        html_content = self._generate_html_report(analysis_results)
        
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"data/analysis/report_{timestamp}.html"
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"보고서가 생성되었습니다: {report_file}")
        return report_file

    def _generate_html_report(self, analysis_results: List[Dict[str, Any]]) -> str:
        """분석 결과를 HTML 형식의 보고서로 생성합니다."""
        papers_html = ""
        for paper in analysis_results:
            paper_link = f"https://arxiv.org/abs/{paper['paper_id']}" if paper['paper_id'] else "#"
            papers_html += f"""
            <div class="paper">
                <h2 class="title">{paper['title']}</h2>
                <div class="tags">
                    {''.join([f'<span class="tag">{tag}</span>' for tag in paper['tags']])}
                </div>
                <div class="summary-section">
                    <h3>요약</h3>
                    {paper['summary']}
                </div>
                <div class="translation-section">
                    <h3>한국어 번역</h3>
                    {paper['translation'] if isinstance(paper['translation'], str) else paper['translation'].get('abstract', '')}
                </div>
                <div class="paper-meta">
                    <div class="paper-date">{paper['submission_date']}</div>
                    <a href="{paper['html_url']}" target="_blank" class="paper-link">논문 보기</a>
                </div>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>논문 분석 보고서</title>
            <style>
                body {{
                    font-family: 'Noto Sans KR', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                
                h1 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                    margin-bottom: 30px;
                }}
                
                h2 {{
                    color: #34495e;
                    margin-top: 30px;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #eee;
                }}
                
                h3 {{
                    color: #7f8c8d;
                    margin-top: 20px;
                }}
                
                .paper {{
                    margin-bottom: 40px;
                    padding: 20px;
                    border: 1px solid #eee;
                    border-radius: 5px;
                    background-color: #fff;
                }}
                
                .paper:hover {{
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    transition: box-shadow 0.3s ease;
                }}
                
                .paper-title {{
                    font-size: 1.4em;
                    color: #2c3e50;
                    margin-bottom: 15px;
                    font-weight: bold;
                }}
                
                .paper-classification {{
                    display: inline-block;
                    background-color: #3498db;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 15px;
                    font-size: 0.9em;
                    margin-bottom: 15px;
                }}
                
                .paper-tags {{
                    margin: 15px 0;
                }}
                
                .tag {{
                    display: inline-block;
                    background-color: #ecf0f1;
                    color: #7f8c8d;
                    padding: 3px 8px;
                    border-radius: 12px;
                    font-size: 0.85em;
                    margin: 3px;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }}
                
                .tag:hover {{
                    background-color: #bdc3c7;
                    color: #2c3e50;
                }}
                
                .paper-summary {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }}
                
                .paper-translation {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    border-left: 4px solid #3498db;
                }}
                
                strong {{
                    color: #333;
                    font-weight: 600;
                }}
                
                blockquote {{
                    margin: 15px 0;
                    padding: 10px 20px;
                    border-left: 4px solid #3498db;
                    background-color: #f8f9fa;
                    color: #666;
                }}
                
                hr {{
                    border: none;
                    border-top: 1px solid #eee;
                    margin: 20px 0;
                }}
                
                p {{
                    margin: 10px 0;
                }}
                
                @media (max-width: 768px) {{
                    body {{
                        padding: 10px;
                    }}
                    
                    .container {{
                        padding: 15px;
                    }}
                    
                    .paper {{
                        padding: 15px;
                    }}
                    
                    .paper-title {{
                        font-size: 1.2em;
                    }}
                }}
                
                .paper-actions {{
                    margin: 15px 0;
                    display: flex;
                    gap: 10px;
                }}
                
                .paper-link {{
                    display: inline-flex;
                    align-items: center;
                    padding: 8px 15px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 0.9em;
                    transition: background-color 0.3s ease;
                }}
                
                .paper-link:hover {{
                    background-color: #2980b9;
                }}
                
                .section-header {{
                    color: #2c3e50;
                    font-size: 1.2em;
                    margin: 20px 0 10px;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #eee;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>논문 분석 보고서</h1>
                <p>분석된 논문 수: {len(analysis_results)}</p>
                
                {papers_html}
            </div>
        </body>
        </html>
        """ 