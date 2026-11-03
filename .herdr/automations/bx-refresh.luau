-- Keeps the Boat snapshots that `bx new` starts from current, and deletes old boxes.
-- `dev` is updated first: every other snapshot is baked from it.
-- Runs on the Mac. `zsh -lc` gives each command the login PATH (bx, boat, gh, jq).
herdr.caps { agents_per_run = 0, tokens_per_day = 0, wall_time = "2h" }

herdr.at("11:00", { tz = "Europe/Paris", days = "mon-fri", name = "refresh" }, function(fire)
  local dev = sh("zsh -lc 'bx update dev'", { check = false, timeout = "30m" })
  if not dev.ok then
    notify("bx refresh: updating dev failed, nothing was baked.\n" .. dev.log_tail)
    return
  end
  local bake = sh("zsh -lc 'bx bake --all'", { check = false, timeout = "75m" })
  if not bake.ok then
    notify("bx refresh: a snapshot did not bake.\n" .. bake.log_tail)
  end
  local gc = sh("zsh -lc 'bx gc --yes'", { check = false, timeout = "5m" })
  if not gc.ok then
    notify("bx refresh: gc failed.\n" .. gc.log_tail)
  end
end)
