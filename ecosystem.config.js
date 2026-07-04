module.exports = {
  apps: [
    {
      name: "artnovabot",
      script: "bot.py",
      // If you are using a virtual environment (venv), point the interpreter to the venv python path:
      interpreter: "./venv/bin/python",
      // Fallback to global python3 if you're not using a virtual environment:
      // interpreter: "python3",
      autorestart: true,
      restart_delay: 5000, // delay restarts by 5s to prevent hammering the server if something is wrong
      watch: false,
      max_memory_restart: "200M"
    }
  ]
};
