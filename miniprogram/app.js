App({
  globalData: {
    // 云开发环境 ID（开通云开发后填入）
    cloudEnv: 'YOUR_CLOUD_ENV_ID'
  },
  onLaunch() {
    if (wx.cloud) {
      wx.cloud.init({ env: this.globalData.cloudEnv, traceUser: true })
    }
  }
})
