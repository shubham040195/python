import os, sys
import hashlib
 
def findDup(folderName):
    dups = {}
    fileList= os.listdir(folderName)
    print('Scanning %s...' % folderName)
    for filename in fileList:
          # Get the path to the file
          path = os.path.join(folderName, filename)
          # Calculate hash for file
          file_hash = hashfile(path)
          # Add or append the file path
          if file_hash in dups:
                dups[file_hash].append(path)
          else:
                dups[file_hash] = [path]
    return dups
 
 
def hashfile(path, blocksize = 65536):
    afile = open(path, 'rb')
    hasher = hashlib.md5()
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    afile.close()
    return hasher.hexdigest()
 
 
def printResults(dict1):
    results = list(filter(lambda x: len(x) > 1, dict1.values()))
    if len(results) > 0:
        print('Duplicates Found:')
        print('The following files are identical. The name could differ, but the content is identical')
        print('*****************')
        for result in results:
            for subresult in result:
                print('\t\t%s' % subresult)
            print('*******************')
 
    else:
        print('No duplicate files found.')
 
 
if __name__ == '__main__':
    if len(sys.argv) > 1:
        dups = {}
        folders = sys.argv[1:]
        for i in folders:
           if os.path.exists(i):
            dups=findDup(i)
           else:
            print('%s is not a valid path, please verify' % i)
            sys.exit()
        printResults(dups)
    else:
        print('Usage: To find the duplicate file present in folder')
