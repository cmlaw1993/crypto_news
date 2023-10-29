from datetime import datetime
import time
import os


def is_time_7pm():
    dt = datetime.now()
    return dt.hour == 19 and dt.minute == 0


def launch():
    code_path = os.path.dirname(os.path.abspath(__file__))
    run_path = os.path.join(code_path, 'run.py')
    log_path = os.path.join(code_path, f'log/{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
    os.system(f'gnome-terminal --maximize -- bash -c "python {run_path} 2>&1 | tee -a {log_path}; exec bash"')


def main():
    while True:
        if is_time_7pm():
            launch()
            time.sleep(120)
        else:
            print('Not yet')
            time.sleep(30)


if __name__ == '__main__':
    main()
