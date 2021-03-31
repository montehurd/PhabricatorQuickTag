
const __setInnerHTML = (selector, html) => {
  document.querySelector(selector).innerHTML = html
  return true
}

const __configurationProjectMouseOver = (e) => {
  e.classList.add('menu_highlighted')
  e.querySelectorAll('div.right_project_menu').forEach(e => e.style.opacity = '100%')
  e.querySelectorAll('button.delete, button.move').forEach(e => e.style.display = 'inline-block')
  return true
}

const __configurationProjectMouseOut = (e) => {
  e.classList.remove('menu_highlighted')
  e.querySelectorAll('div.right_project_menu').forEach(e => e.style.opacity = '50%')
  e.querySelectorAll('button.delete, button.move').forEach(e => e.style.display = 'none')
  return true
}

const __setPhabricatorUrl = (url) => {
  document.querySelector('input[name=phabricator_url]').value = url
  return true
}

const __getPhabricatorUrl = () => {
  return document.querySelector('input[name=phabricator_url]').value
}

const __setPhabricatorToken = (token) => {
  document.querySelector('input[name=phabricator_token]').value = token
  return true
}

const __getPhabricatorToken = () => {
  return document.querySelector('input[name=phabricator_token]').value
}

const __setUpstreamCSSLinkURL = (url) => {
  document.querySelector('link#upstream_css_link').href = url
  return true
}

const __setUpstreamBaseURL = (url) => {
  document.querySelector('base#upstream_base').href = url
  return true
}

const __showTickets = () => {
  document.querySelector('div.projects_tickets').style.visibility = 'visible'
  return true
}

const __hideTickets = () => {
  document.querySelector('div.projects_tickets').style.visibility = 'hidden'
  return true
}

const __showModalOverlay = () => {
  document.querySelector('div.modal_overlay').style.display = 'block'
  return true
}

const __hideModalOverlay = () => {
  document.querySelector('div.modal_overlay').style.display = 'none'
  return true
}

const __hideProjectSearch = () => {
  document.querySelector('div.projects_search_centered_panel').style.display = 'none'
  __hideModalOverlay()
  return true
}

const __showProjectSearch = (projectTypeName, title) => {
  __showModalOverlay()
  document.querySelector('div.projects_search_centered_panel').style.display = 'block'
  document.querySelector('div.projects_search_title').innerHTML = title
  document.querySelector('input#projects_search_project_type_name').value = projectTypeName
  document.querySelector('input#projects_search_textbox').focus()
  return true
}

const __hideAlert = () => {
  document.querySelector('div.alert_panel').style.display = 'none'
  __hideModalOverlay()
  return true
}

const __showAlert = (title, description) => {
  __showModalOverlay()
  document.querySelector('div.alert_panel').style.display = 'block'
  document.querySelector('div.alert_panel_title').innerHTML = title
  document.querySelector('div.alert_panel_description').innerHTML = description
  return true
}

const __hideLoadingIndicator = () => {
  document.querySelector('div.loading_indicator_panel').style.display = 'none'
  __hideModalOverlay()
  return true
}

const __showLoadingIndicator = () => {
  __showModalOverlay()
  document.querySelector('div.loading_indicator_panel').style.display = 'block'
  return true
}

const __resetProjectSearch = () => {
  document.querySelector('input#projects_search_project_type_name').value = ''
  document.querySelector('input#projects_search_textbox').value = ''
  document.querySelector('div.projects_search_results').innerHTML = ''
  return true
}

const __deleteMenu = (buttonID) => {
  const thisButton = document.querySelector(`button#${buttonID}`)
  const menuDiv = thisButton.closest('div.menu')
  menuDiv.remove()
  return true
}

const __toggleButton = (buttonID) => {
  if (__isButtonSelected(buttonID)) {
    __deselectButton(buttonID)
  } else {
    __selectButton(buttonID)
  }
  return true
}

const __getComment = (ticketID) => {
  return document.querySelector(`textarea#ticketID${ticketID}`).value
}

const __setComment = (ticketID, comment) => {
  const textArea = document.querySelector(`textarea#ticketID${ticketID}`)
  textArea.value = comment
  return textArea.value
}

const __deselectOtherButtonsInMenu = (buttonID) => {
  const thisButton = document.querySelector(`button#${buttonID}`)
  const menu = thisButton.closest('buttonmenu')
  if (thisButton.parentElement != menu) {
    pywebview.api.printDebug("Closest 'buttonmenu' tag is not button tag's parent")
  }
  menu.querySelectorAll('button').forEach(button => {
    if (button.id == thisButton.id) return
    button.classList.remove('selected')
  })
  return true
}

const __setTicketActionMessage = (ticketID, message) => {
  const span = document.querySelector(`span#buttonActionMessage${ticketID}`)
  span.innerHTML = message
  setTimeout(() => {{ span.innerHTML = '' }}, 1500)
  return true
}

const __isButtonSelected = (buttonID) => {
  return document.querySelector(`button#${buttonID}`).classList.contains('selected')
}

const __selectButton = (buttonID) => {
  document.querySelector(`button#${buttonID}`).classList.add('selected')
  return true
}

const __deselectButton = (buttonID) => {
  document.querySelector(`button#${buttonID}`).classList.remove('selected')
  return true
}

const __show_save_url_and_token_button = () => {
  pywebview.api.isSavedURLAndTokenSameAsInTextboxes().then(isNoChange => {
    document.querySelector('button.save_url_and_token').style.display = isNoChange ? 'none' : 'inline-block'
  })
  return true
}

const __showProjectsConfigurationBody = shouldShow => {
  document.querySelector('div.projects_configuration_body').style.display = shouldShow ? 'block' : 'none'
  return true
}
