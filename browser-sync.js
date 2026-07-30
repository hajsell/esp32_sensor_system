module.exports = {
  proxy: "http://app:5000",
  files: [
    "frontend/templates/**/*.html",
    "frontend/static/**/*.css",
    "frontend/static/**/*.js",
    "app/**/*.py",
    "run.py",
  ],
  watchOptions: {
    usePolling: true,
    interval: 500,
    ignoreInitial: true,
  },
  host: "0.0.0.0",
  port: 3000,
  ui: {
    port: 3001,
  },
  open: false,
  notify: false,
  reloadDelay: 500,
};
