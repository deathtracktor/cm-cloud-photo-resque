Resque your valuable photos from the CM Cloud before it's too late!
-------------------------------------------------------------------

Use this utility to resque your photographs from `CM Cloud`,
the default backup option of the excellent `QuickPic` image browser for Android.
You can also use Windows-only, closed-source [CM Cloud download tool](https://cloud.cmcm.com/client_cloud_res/cmqp/resource/tool/cloud_gallery_download.exe),
if you prefer.


## Pre-requisites

* [Python 3.6](https://www.python.org/downloads/release/python-364/) interpreter with `pip` command

## Installation

* Clone the repository
* Install dependencies

  ```
  pip install -r requirements.txt
  ```
* Run the application

  ```
  python download_all.py
  ```
  
## Notes

* Images get downloaded to the current working directory for simplicity sake.
* Only JPEG format is supported.
* The utility supports incremental downloads (it won't overwrite any previously downloaded stuff).
* Use at your own risk! I warned you.

  