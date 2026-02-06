sub init()
  m.selectorGroup = m.top.findNode("selectorGroup")
  m.formGroup = m.top.findNode("formGroup")
  m.accountList = m.top.findNode("accountList")
  m.addAccountButton = m.top.findNode("addAccountButton")
  m.accountForm = m.top.findNode("accountForm")
  m.usernameField = m.accountForm.findNode("usernameField")
  m.passwordField = m.accountForm.findNode("passwordField")
  m.urlField = m.accountForm.findNode("urlField")
  m.saveAccountButton = m.top.findNode("saveAccountButton")
  m.cancelAccountButton = m.top.findNode("cancelAccountButton")
  m.authSpinner = m.top.findNode("authSpinner")
  m.authError = m.top.findNode("authError")

  m.accounts = loadAccounts()
  populateAccountList()
  m.mode = "selector"
  setSelectorFocus()
end sub

function onKeyEvent(key as String, press as Boolean) as Boolean
  if press = false then return false

  if m.mode = "selector"
    if key = "down"
      if m.selectorFocus = "list"
        m.selectorFocus = "add"
        m.addAccountButton.setFocus(true)
        return true
      end if
    else if key = "up"
      if m.selectorFocus = "add"
        m.selectorFocus = "list"
        m.accountList.setFocus(true)
        return true
      end if
    else if key = "OK"
      if m.selectorFocus = "list"
        selectFocusedAccount()
        return true
      else if m.selectorFocus = "add"
        showForm()
        return true
      end if
    end if
  else if m.mode = "form"
    if key = "down"
      m.formFocusIndex = (m.formFocusIndex + 1) mod m.formFocusOrder.count()
      applyFormFocus()
      return true
    else if key = "up"
      m.formFocusIndex = (m.formFocusIndex - 1 + m.formFocusOrder.count()) mod m.formFocusOrder.count()
      applyFormFocus()
      return true
    else if key = "OK"
      focusNode = m.formFocusOrder[m.formFocusIndex]
      if focusNode = m.saveAccountButton
        saveAccount()
        return true
      else if focusNode = m.cancelAccountButton
        showSelector()
        return true
      end if
    end if
  end if

  return false
end function

sub setSelectorFocus()
  if m.accounts.count() > 0
    m.selectorFocus = "list"
    m.accountList.setFocus(true)
  else
    m.selectorFocus = "add"
    m.addAccountButton.setFocus(true)
  end if
end sub

sub showForm()
  m.mode = "form"
  m.selectorGroup.visible = false
  m.formGroup.visible = true
  m.authError.text = ""
  m.usernameField.text = ""
  m.passwordField.text = ""
  m.urlField.text = ""
  m.formFocusOrder = [m.usernameField, m.passwordField, m.urlField, m.saveAccountButton, m.cancelAccountButton]
  m.formFocusIndex = 0
  applyFormFocus()
end sub

sub showSelector()
  m.mode = "selector"
  m.formGroup.visible = false
  m.selectorGroup.visible = true
  m.authError.text = ""
  setSelectorFocus()
end sub

sub applyFormFocus()
  node = m.formFocusOrder[m.formFocusIndex]
  node.setFocus(true)
end sub

sub selectFocusedAccount()
  if m.accounts.count() = 0 then return
  index = m.accountList.itemFocused
  if index < 0 or index >= m.accounts.count() then return
  account = m.accounts[index]
  completeLogin(account)
end sub

sub saveAccount()
  username = m.usernameField.text
  password = m.passwordField.text
  url = m.urlField.text
  if username = "" or password = "" or url = ""
    m.authError.text = "Veuillez remplir tous les champs."
    return
  end if

  account = {
    username: username
    password: password
    url: url
  }
  m.accounts.push(account)
  persistAccounts()
  completeLogin(account)
end sub

sub completeLogin(account as Object)
  m.authSpinner.visible = false
  m.top.loginUsername = account.username
  m.top.loginPassword = account.password
  m.top.loginUrl = account.url
  m.top.loginResult = "success"
end sub

sub populateAccountList()
  root = CreateObject("roSGNode", "ContentNode")
  for each account in m.accounts
    node = CreateObject("roSGNode", "ContentNode")
    node.title = account.username
    node.shortDescriptionLine1 = account.url
    root.appendChild(node)
  end for
  m.accountList.content = root
end sub

function loadAccounts() as Object
  registry = CreateObject("roRegistrySection", "accounts")
  stored = registry.Read("list")
  if stored = invalid or stored = "" then return []
  parsed = ParseJson(stored)
  if parsed = invalid then return []
  return parsed
end function

sub persistAccounts()
  registry = CreateObject("roRegistrySection", "accounts")
  registry.Write("list", FormatJson(m.accounts))
  registry.Flush()
end sub
