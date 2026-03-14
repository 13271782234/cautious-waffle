from mistake_notebook import MistakeNotebook
from datetime import datetime
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    print("\n" + "="*50)
    print("           智能错题本管理系统")
    print("="*50)
    print("1. 添加新错题")
    print("2. 查看今日复习任务")
    print("3. 搜索错题")
    print("4. 查看统计信息")
    print("5. 生成学习图表")
    print("6. 导出错题集为PDF")
    print("7. 个性化设置")
    print("8. 查看高频错误推荐")
    print("0. 退出系统")
    print("="*50)

def add_mistake_ui(notebook):
    print("\n--- 添加新错题 ---")
    subject = input("请输入科目: ")
    knowledge_point = input("请输入知识点: ")
    question = input("请输入题目内容: ")
    answer = input("请输入正确答案: ")
    analysis = input("请输入题目解析: ")
    error_reason = input("请输入错误原因: ")
    
    notebook.add_mistake(subject, knowledge_point, question, answer, analysis, error_reason)

def view_reviews_ui(notebook):
    print("\n--- 今日复习任务 ---")
    reviews = notebook.get_today_reviews()
    if len(reviews) == 0:
        print("太棒了！今天没有需要复习的错题！")
        return
        
    print(f"今日共有 {len(reviews)} 道题需要复习:")
    print("-" * 40)
    for _, row in reviews.iterrows():
        print(f"\nID: {row['id']}")
        print(f"科目: {row['subject']} | 知识点: {row['knowledge_point']}")
        print(f"题目: {row['question'][:50]}..." if len(row['question']) > 50 else f"题目: {row['question']}")
        print(f"已复习次数: {row['review_count']} | 掌握程度: {row['mastery_level']}/5")
        
    while True:
        choice = input("\n是否要标记某题已复习? (输入ID或n取消): ")
        if choice.lower() == 'n':
            break
        try:
            mid = int(choice)
            score = int(input("请为本次复习表现打分(1-10分): "))
            notebook.mark_reviewed(mid, score)
        except ValueError:
            print("请输入有效的数字")

def search_ui(notebook):
    print("\n--- 搜索错题 ---")
    keyword = input("请输入搜索关键词: ")
    results = notebook.search_mistakes(keyword)
    if len(results) == 0:
        print("未找到相关错题")
        return
        
    print(f"找到 {len(results)} 条相关记录:")
    for _, row in results.iterrows():
        print(f"\nID: {row['id']} | 科目: {row['subject']} | 知识点: {row['knowledge_point']}")
        print(f"题目: {row['question']}")

def statistics_ui(notebook):
    print("\n--- 统计信息 ---")
    stats = notebook.get_statistics()
    print(f"总题数: {stats['total_mistakes']}")
    print(f"待复习题数: {stats['pending_reviews']}")
    print("\n按科目分布:")
    for subject, count in stats['by_subject'].items():
        print(f"  {subject}: {count}题")
    print("\n掌握程度分布:")
    for level, count in stats['mastery_distribution'].items():
        print(f"  Level {level}: {count}题")

def plot_ui(notebook):
    print("\n--- 生成学习图表 ---")
    print("1. 科目分布柱状图")
    print("2. 掌握程度趋势图")
    choice = input("请选择图表类型: ")
    
    if choice == '1':
        save = input("是否保存图片? (y/n): ")
        if save.lower() == 'y':
            notebook.plot_subject_distribution("subject_distribution.png")
        else:
            notebook.plot_subject_distribution()
    elif choice == '2':
        save = input("是否保存图片? (y/n): ")
        if save.lower() == 'y':
            notebook.plot_mastery_progress("mastery_progress.png")
        else:
            notebook.plot_mastery_progress()
    else:
        print("无效选择")

def export_pdf_ui(notebook):
    print("\n--- 导出PDF ---")
    subject = input("请输入要导出的科目(留空导出全部): ")
    filename = input("请输入输出文件名(默认: mistake_notebook.pdf): ")
    if not filename:
        filename = "mistake_notebook.pdf"
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    
    if subject:
        notebook.export_to_pdf(filename, subject)
    else:
        notebook.export_to_pdf(filename)

def settings_ui(notebook):
    print("\n--- 个性化设置 ---")
    print(f"当前复习周期: {notebook.config['custom_review_intervals']}天")
    change = input("是否修改复习周期? (y/n): ")
    if change.lower() == 'y':
        intervals_str = input("请输入复习周期(用逗号分隔天数, 如: 1,2,4,7,15): ")
        try:
            intervals = [int(x.strip()) for x in intervals_str.split(',')]
            notebook.set_custom_review_intervals(intervals)
        except ValueError:
            print("输入格式错误")

def recommendations_ui(notebook):
    print("\n--- 高频错误与学习推荐 ---")
    freq = notebook.get_high_frequency_errors(3)
    print("高频错误知识点:")
    for kp, count in freq.items():
        print(f"  {kp}: {count}次错误")
    
    print("\n学习建议:")
    recs = notebook.recommend_resources()
    for rec in recs:
        print(f"  - {rec['建议']}")

def main():
    notebook = MistakeNotebook()
    print(f"已加载错题本，当前共有 {len(notebook.df)} 道错题")
    
    while True:
        print_menu()
        choice = input("请选择操作: ")
        
        if choice == '1':
            add_mistake_ui(notebook)
        elif choice == '2':
            view_reviews_ui(notebook)
        elif choice == '3':
            search_ui(notebook)
        elif choice == '4':
            statistics_ui(notebook)
        elif choice == '5':
            plot_ui(notebook)
        elif choice == '6':
            export_pdf_ui(notebook)
        elif choice == '7':
            settings_ui(notebook)
        elif choice == '8':
            recommendations_ui(notebook)
        elif choice == '0':
            print("保存数据中...")
            notebook.save_data()
            print("感谢使用智能错题本！再见！")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
