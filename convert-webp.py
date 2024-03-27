#!/usr/bin/python3
import pathlib, subprocess, sys, shlex, logging, shutil, os

logger = logging.getLogger('webp')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[WebPConverter] %(levelname)s : %(message)s')
streamhandler = logging.StreamHandler()
streamhandler.setFormatter(formatter)
logger.addHandler(streamhandler)

def getFileMimeType(comic_file):
    command = shlex.split(f"file -b --mime-type {comic_file}")
    try:
        rar_mime = ['application/vnd.rar', 'application/x-rar-compressed', 'application/x-rar', 'application/rar', 'application/x-x-rar']
        zip_mime = ['application/zip', 'application/x-zip-compressed', 'multipart/x-zip']
        output = subprocess.check_output(command).decode('utf-8').strip('\n')
        logger.debug(f"MIME type detected: {output}")  # Added this line for logging
        if output in rar_mime:
            rar_mime = 'rar'
            return rar_mime
        else output in zip_mime:
            zip_mime = 'zip'
            return zip_mime
    except subprocess.CalledProcessError as e:
        logger.error(f"Error in Compression subprocess: {e.stderr}")

def createWorkDir(filename):
    cwd = pathlib.Path(os.getenv('C2W_PATH','D:\Books\Comics\TOOLS\Mylar3\mylar3-master\cache'))
    # Quick and dirty fix for shlex.quote being inflexible... Thanks for appearing Li'l Empire.
    work_path = cwd.joinpath("work",filename.stem.replace("'",""))
    logger.info(f"Working directory: {work_path}")
    try:
        work_path.mkdir(mode=0o775,parents=True)
    except FileExistsError as fee:
        logger.info(f"Working directory already exists. Cleaning up.")
        shutil.rmtree(work_path)
        work_path.mkdir(mode=0o775,parents=True)
    return work_path

def extractComicFile(work_path,filename:pathlib.Path):
    logger.info(f"Extracting {filename.resolve()} to {work_path.resolve()}")
    try:
        work_path = shlex.quote(str(work_path.resolve()))
        comic_file = shlex.quote(str(filename.resolve()))
        filetype = getFileMimeType(comic_file)
        print(filetype)
        if filetype == 'zip':
            command = shlex.split(f"7z e -o{work_path} {comic_file}")
        elif filetype == 'rar':
            command = shlex.split(f"unrar e {comic_file} {work_path}")
        else:
            raise AttributeError(f"File cannot be identified... Mime-Type: {filetype}")
        subprocess.run(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        logger.error(f"Extraction error: [{e.returncode}] {e.stderr}")

def getFilesToConvert(work_path):
    return work_path.iterdir()

def convertToWebP(files:list):
    logger.info("Starting conversion")
    valid_ext = [".jpg",".jpeg", ".jxl", ".png", ".gif"]
    for file in files:
        if file.suffix.lower() in valid_ext:
            logger.info(f"Conversion of {file.name} started")
            try:
                # Dirty fix for shlex.quote barfing on filepaths with apostrophs
                if "'" in str(file.resolve()):
                    old_file = file
                    file = pathlib.Path(str(old_file.resolve()).replace("'",""))
                    os.rename(str(old_file.resolve()),str(file.resolve()))
                logger.debug(file.resolve())
                file_path = shlex.quote(str(file.resolve()))
                out_path = shlex.quote(f"{str(work_path)}/{file.stem}.webp")
                if file.suffix.lower() == ".gif":
                    command = shlex.split(f"gif2webp {file_path} -quiet -q 80 -o {out_path}")
                else:
                    command = shlex.split(f"cwebp {file_path} -quiet -q 80 -o {out_path}")
                logger.debug(command)
                subprocess.call(command)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error in Conversion Process: [{e.returncode}] {e.stderr}")

def createProcessedComic(work_path,output_path):
    logger.info(f"Creating converted file under {output_path}")
    if not output_path.parent.exists():
        output_path.mkdir(0o775)
    if output_path.exists():
        output_path.unlink()
    output_file = shlex.quote(f"{str(output_path.absolute())[:-1]}z")
    cwd = shlex.quote(str(work_path.resolve()))
    command = shlex.split(f"7z a -tzip {output_file} {cwd}/*.webp {cwd}/*.xml")
    try:
        subprocess.call(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error in Compression subprocess: {e.stderr}")


def cleanUp(work_path):
    shutil.rmtree(work_path.absolute(),True)

if __name__ == "__main__":
    comic_file = pathlib.Path(sys.argv[4])
    logger.info(f"Converting {comic_file.resolve()}")
    work_path = createWorkDir(comic_file)
    extractComicFile(work_path, comic_file)
    files = getFilesToConvert(work_path)
    convertToWebP(files)
    createProcessedComic(work_path, comic_file)
    logger.info(f"Conversion finished") 
    cleanUp(work_path)
