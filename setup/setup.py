import os

def symlink_file(src, dst):

    # Check if the symlink already exists and unlink it if it does
    if os.path.islink(dst):
        try:
            os.unlink(dst)
        except:
            raise Exception(f"Error removing existing symlink: {dst}")

    # Create a new symbolic link
    try:
        os.symlink(src, dst)
        print(f'Created symlink: {dst}')
    except:
        raise Exception(f"Error creating symlink: {dst}")


if __name__ == "__main__":

    curr_path = os.path.dirname(os.path.abspath(__file__))
    code_path = os.path.join(curr_path, "..")

    # Install python requirements

    os.system(f'pip install -r  {os.path.join(curr_path, "data/requirements.txt")}')

    # Setup data symlinks

    data_path = os.path.join(code_path, 'data')

    if not os.path.exists(data_path):
        os.makedirs(data_path)

    symlink_file('/mnt/CryptoNewsData/log', f'{os.path.join(data_path, "log")}')
    symlink_file('/mnt/CryptoNewsData/staticdata', f'{os.path.join(data_path, "staticdata")}')
    symlink_file('/mnt/CryptoNewsData/vardata', f'{os.path.join(data_path, "vardata")}')
    symlink_file('/mnt/CryptoNewsData/vectordb', f'{os.path.join(data_path, "vectordb")}')
