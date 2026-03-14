import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
import json

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("警告: reportlab库未安装，PDF导出功能将不可用")
    print("请执行: pip install reportlab")

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]

class MistakeNotebook:
    def __init__(self, data_file="mistake_data.csv", config_file="config.json"):
        self.data_file = data_file
        self.config_file = config_file
        self.columns = [
            'id', 'subject', 'knowledge_point', 'question', 'answer',
            'analysis', 'error_reason', 'create_time', 'review_count',
            'next_review_time', 'mastery_level'
        ]
        self.df = self._load_data()
        self.config = self._load_config()
        
    def _load_data(self):
        if os.path.exists(self.data_file):
            df = pd.read_csv(self.data_file, encoding='utf-8')
            df['create_time'] = pd.to_datetime(df['create_time'])
            df['next_review_time'] = pd.to_datetime(df['next_review_time'])
            return df
        else:
            return pd.DataFrame(columns=self.columns)
            
    def _load_config(self):
        default_config = {
            'custom_review_intervals': EBBINGHAUS_INTERVALS,
            'theme': 'default',
            'auto_backup': True
        }
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                default_config.update(loaded)
        return default_config
        
    def save_data(self):
        self.df.to_csv(self.data_file, index=False, encoding='utf-8')
        if self.config.get('auto_backup', True):
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d')}_{self.data_file}"
            self.df.to_csv(backup_name, index=False, encoding='utf-8')
            
    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
            
    def add_mistake(self, subject, knowledge_point, question, answer, analysis, error_reason):
        new_id = len(self.df) + 1 if len(self.df) > 0 else 1
        now = datetime.now()
        next_review = now + timedelta(days=self.config['custom_review_intervals'][0])
        
        new_row = {
            'id': new_id,
            'subject': subject,
            'knowledge_point': knowledge_point,
            'question': question,
            'answer': answer,
            'analysis': analysis,
            'error_reason': error_reason,
            'create_time': now,
            'review_count': 0,
            'next_review_time': next_review,
            'mastery_level': 0
        }
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self.save_data()
        print(f"错题已添加，ID为: {new_id}")
        return new_id
        
    def get_today_reviews(self):
        today = datetime.now().date()
        mask = self.df['next_review_time'].dt.date <= today
        return self.df[mask].copy()
        
    def mark_reviewed(self, mistake_id, performance_score):
        idx = self.df[self.df['id'] == mistake_id].index
        if len(idx) == 0:
            print(f"未找到ID为{mistake_id}的错题")
            return False
            
        self.df.loc[idx, 'review_count'] += 1
        review_count = self.df.loc[idx, 'review_count'].values[0]
        
        if performance_score >= 8:
            new_mastery = min(5, self.df.loc[idx, 'mastery_level'].values[0] + 1)
            self.df.loc[idx, 'mastery_level'] = new_mastery
        elif performance_score <= 3:
            new_mastery = max(0, self.df.loc[idx, 'mastery_level'].values[0] - 1)
            self.df.loc[idx, 'mastery_level'] = new_mastery
            
        intervals = self.config['custom_review_intervals']
        current_interval_idx = min(review_count, len(intervals) - 1)
        next_days = intervals[current_interval_idx]
        
        self.df.loc[idx, 'next_review_time'] = datetime.now() + timedelta(days=next_days)
        self.save_data()
        print(f"错题{mistake_id}已标记为已复习，下次复习时间: {self.df.loc[idx, 'next_review_time'].values[0]}")
        return True
        
    def search_mistakes(self, keyword):
        mask = (
            self.df['question'].str.contains(keyword, na=False, case=False) |
            self.df['analysis'].str.contains(keyword, na=False, case=False) |
            self.df['knowledge_point'].str.contains(keyword, na=False, case=False) |
            self.df['subject'].str.contains(keyword, na=False, case=False)
        )
        return self.df[mask].copy()
        
    def get_statistics(self):
        stats = {}
        stats['total_mistakes'] = len(self.df)
        stats['by_subject'] = self.df['subject'].value_counts().to_dict()
        stats['by_knowledge'] = self.df['knowledge_point'].value_counts().to_dict()
        stats['mastery_distribution'] = self.df['mastery_level'].value_counts().sort_index().to_dict()
        stats['pending_reviews'] = len(self.get_today_reviews())
        return stats
        
    def plot_subject_distribution(self, save_path=None):
        stats = self.get_statistics()
        subjects = list(stats['by_subject'].keys())
        counts = list(stats['by_subject'].values())
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(subjects, counts, color='skyblue')
        ax.set_xlabel('科目')
        ax.set_ylabel('错题数量')
        ax.set_title('错题按科目分布')
        ax.bar_label(bars)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        plt.show()
        
    def plot_mastery_progress(self, save_path=None):
        stats = self.get_statistics()
        levels = sorted(stats['mastery_distribution'].keys())
        counts = [stats['mastery_distribution'].get(l, 0) for l in levels]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(levels, counts, marker='o', linewidth=2, color='green')
        ax.fill_between(levels, counts, alpha=0.3, color='green')
        ax.set_xlabel('掌握程度 (0-5)')
        ax.set_ylabel('错题数量')
        ax.set_title('掌握程度分布')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        plt.show()
        
    def set_custom_review_intervals(self, intervals):
        if isinstance(intervals, list) and all(isinstance(i, int) for i in intervals):
            self.config['custom_review_intervals'] = sorted(intervals)
            self.save_config()
            print(f"复习周期已设置为: {self.config['custom_review_intervals']}天")
        else:
            print("请提供整数列表形式的复习周期")
            
    def export_to_pdf(self, output_path="mistake_notebook.pdf", filter_subject=None):
        if not PDF_SUPPORT:
            print("请先安装reportlab库: pip install reportlab")
            return False
            
        df_export = self.df.copy()
        if filter_subject:
            df_export = df_export[df_export['subject'] == filter_subject]
            
        if len(df_export) == 0:
            print("没有找到要导出的错题")
            return False
            
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        y_position = height - 50
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y_position, "智能错题本")
        y_position -= 30
        
        c.setFont("Helvetica", 10)
        c.drawString(50, y_position, f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        y_position -= 20
        c.drawString(50, y_position, f"总题数: {len(df_export)}")
        y_position -= 40
        
        for _, row in df_export.iterrows():
            if y_position < 100:
                c.showPage()
                y_position = height - 50
                
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, f"ID: {row['id']} | 科目: {row['subject']} | 知识点: {row['knowledge_point']}")
            y_position -= 20
            
            c.setFont("Helvetica", 10)
            question_lines = self._wrap_text(f"题目: {row['question']}", 80)
            for line in question_lines:
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50
                c.drawString(50, y_position, line)
                y_position -= 15
                
            answer_lines = self._wrap_text(f"答案: {row['answer']}", 80)
            for line in answer_lines:
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50
                c.drawString(50, y_position, line)
                y_position -= 15
                
            analysis_lines = self._wrap_text(f"解析: {row['analysis']}", 80)
            for line in analysis_lines:
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50
                c.drawString(50, y_position, line)
                y_position -= 15
                
            c.drawString(50, y_position, "-" * 80)
            y_position -= 30
            
        c.save()
        print(f"PDF已导出到: {output_path}")
        return True
        
    def _wrap_text(self, text, max_chars):
        lines = []
        current_line = ""
        for char in str(text):
            current_line += char
            if len(current_line) >= max_chars:
                lines.append(current_line)
                current_line = ""
        if current_line:
            lines.append(current_line)
        return lines
        
    def get_high_frequency_errors(self, top_n=5):
        knowledge_counts = self.df['knowledge_point'].value_counts()
        return knowledge_counts.head(top_n).to_dict()
        
    def recommend_resources(self):
        freq_errors = self.get_high_frequency_errors(3)
        recommendations = []
        for kp in freq_errors.keys():
            recommendations.append({
                '知识点': kp,
                '建议': f"重点复习'{kp}'相关内容，建议多做同类型题目巩固"
            })
        return recommendations
