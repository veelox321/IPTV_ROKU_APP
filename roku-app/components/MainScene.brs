sub init()
  m.splashView = m.top.findNode("splashView")
  m.loginView = m.top.findNode("loginView")
  m.homeView = m.top.findNode("homeView")
  m.playbackView = m.top.findNode("playbackView")
  m.loadingTextTimer = m.top.findNode("loadingTextTimer")

  m.loadingTextTimer.observeField("fire", "onLoadingTextTimer")
  m.loadingTextTimer.control = "start"

  m.loginView.observeField("loginResult", "onLoginResult")
  m.homeView.observeField("requestPlayback", "onRequestPlayback")
  m.homeView.observeField("exitPlayback", "onExitPlayback")

  checkCredentials()
end sub

sub checkCredentials()
  registry = CreateObject("roRegistrySection", "auth")
  username = registry.Read("username")
  token = registry.Read("token")

  if username <> invalid and username <> "" and token <> invalid and token <> ""
    showHome()
  else
    showLogin()
  end if
end sub

sub showLogin()
  m.splashView.visible = false
  m.homeView.visible = false
  m.playbackView.visible = false
  m.loginView.visible = true
  m.loginView.setFocus(true)
end sub

sub showHome()
  m.splashView.visible = false
  m.loginView.visible = false
  m.playbackView.visible = false
  m.homeView.visible = true
  m.homeView.setFocus(true)
end sub

sub onLoginResult()
  if m.loginView.loginResult = "success"
    registry = CreateObject("roRegistrySection", "auth")
    registry.Write("username", m.loginView.loginUsername)
    registry.Write("token", "demo-token")
    registry.Flush()
    showHome()
  end if
end sub

sub onLoadingTextTimer()
  if m.splashView.visible
    m.splashView.showLoadingText = true
  end if
end sub

sub onRequestPlayback()
  if m.homeView.requestPlayback = true
    m.playbackView.visible = true
    m.homeView.visible = false
    m.playbackView.setFocus(true)
    m.homeView.requestPlayback = false
  end if
end sub

sub onExitPlayback()
  if m.homeView.exitPlayback = true
    m.playbackView.visible = false
    m.homeView.visible = true
    m.homeView.setFocus(true)
  end if
end sub

function onKeyEvent(key as String, press as Boolean) as Boolean
  if press = false then return false

  if m.playbackView.visible and key = "back"
    m.playbackView.visible = false
    m.homeView.visible = true
    m.homeView.setFocus(true)
    return true
  end if

  return false
end function
