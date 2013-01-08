BUILD_LOG=./build_log
echo "Build Starting: `date`" &> ${BUILD_LOG}
python bos.py --config ./bos.cfg &>> ${BUILD_LOG}
echo "Build Finished: `date`" &>> ${BUILD_LOG}
