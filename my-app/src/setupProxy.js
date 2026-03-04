const { createProxyMiddleware } = require('http-proxy-middleware')

module.exports = function (app) {
  app.use(
    '/api/nvidia',
    createProxyMiddleware({
      target: 'https://integrate.api.nvidia.com',
      changeOrigin: true,
      pathRewrite: { '^/api/nvidia': '/v1' },
      secure: true,
    })
  )

  app.use(
    '/api/grok',
    createProxyMiddleware({
      target: 'http://localhost:6969',
      changeOrigin: true,
      pathRewrite: { '^/api/grok': '' },
      secure: false,
    })
  )
}
