sub init()
  m.form = m.top.findNode("loginForm")
  m.usernameField = m.form.findNode("usernameField")
  m.passwordField = m.form.findNode("passwordField")
  m.deviceCodeButton = m.form.findNode("deviceCodeButton")
  m.rememberMeButton = m.form.findNode("rememberMeButton")
  m.loginButton = m.form.findNode("loginButton")
  m.authSpinner = m.top.findNode("authSpinner")
  m.authError = m.top.findNode("authError")

  m.focusOrder = [m.usernameField, m.passwordField, m.deviceCodeButton, m.rememberMeButton, m.loginButton]
  m.focusIndex = 0
  m.rememberEnabled = false
  m.deviceCodeMode = false

  applyFocus()
end sub

function onKeyEvent(key as String, press as Boolean) as Boolean
  if press = false then return false

  if key = "down"
    m.focusIndex = (m.focusIndex + 1) mod m.focusOrder.count()
    applyFocus()
    return true
  else if key = "up"
    m.focusIndex = (m.focusIndex - 1 + m.focusOrder.count()) mod m.focusOrder.count()
    applyFocus()
    return true
  else if key = "OK"
    if m.focusOrder[m.focusIndex] = m.deviceCodeButton
      m.deviceCodeMode = not m.deviceCodeMode
      updateDeviceCodeText()
      return true
    else if m.focusOrder[m.focusIndex] = m.rememberMeButton
      m.rememberEnabled = not m.rememberEnabled
      updateRememberText()
      return true
    else if m.focusOrder[m.focusIndex] = m.loginButton
      attemptLogin()
      return true
    end if
  end if

  return false
end function

sub applyFocus()
  node = m.focusOrder[m.focusIndex]
  node.setFocus(true)
end sub

sub updateRememberText()
  if m.rememberEnabled
    m.rememberMeButton.text = "Remember login: On"
  else
    m.rememberMeButton.text = "Remember login: Off"
  end if
end sub

sub updateDeviceCodeText()
  if m.deviceCodeMode
    m.deviceCodeButton.text = "Using Device Code"
  else
    m.deviceCodeButton.text = "Use Device Code"
  end if
end sub

sub attemptLogin()
  m.authError.text = ""
  m.authSpinner.visible = true

  if m.deviceCodeMode
    completeLogin("device-code-user")
  else
    username = m.usernameField.text
    password = m.passwordField.text
    if username = "" or password = ""
      m.authSpinner.visible = false
      m.authError.text = "Please enter both username and password."
      return
    end if
    completeLogin(username)
  end if
end sub

sub completeLogin(username as String)
  m.authSpinner.visible = false
  m.top.loginUsername = username
  m.top.loginResult = "success"
end sub
