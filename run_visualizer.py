import argparse
from job_visualizer import JobVisualizer

def main():
    parser = argparse.ArgumentParser(description='Job Market Data Visualizer')
    parser.add_argument('--mode', choices=['dashboard', 'report', 'excel'], 
                       default='dashboard',
                       help='Visualization mode (default: dashboard)')
    parser.add_argument('--output', type=str,
                       help='Output file path for report or Excel export')
    
    args = parser.parse_args()
    visualizer = JobVisualizer()
    
    if args.mode == 'dashboard':
        visualizer.create_dashboard()
    elif args.mode == 'report':
        output_file = args.output or 'job_report.html'
        visualizer.create_report(output_file)
        print(f"Report generated: {output_file}")
    elif args.mode == 'excel':
        output_file = args.output or 'jobs.xlsx'
        visualizer.export_to_excel(output_file)
        print(f"Excel file generated: {output_file}")

if __name__ == '__main__':
    main() 