
const __setInnerHTML = (selector, html) => {
  document.querySelector(selector).innerHTML = html
  return true
}

const __configurationProjectMouseOver = (e) => {
  e.classList.add('menu_highlighted')
  e.querySelectorAll('div.right_project_menu').forEach(e => e.style.opacity = '100%')
  e.querySelectorAll('button.delete, button.move-up, button.move-down, button.select-all, button.select-none').forEach(e => e.style.display = 'inline-block')
  return true
}

const __configurationProjectMouseOut = (e) => {
  e.classList.remove('menu_highlighted')
  e.querySelectorAll('div.right_project_menu').forEach(e => e.style.opacity = '50%')
  e.querySelectorAll('button.delete, button.move-up, button.move-down, button.select-all, button.select-none').forEach(e => e.style.display = 'none')
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

const __swapElements = (element1, element2) => {
  const afterNode2 = element2.nextElementSibling
  const parent = element2.parentElement
  if (element1 === afterNode2) {
    parent.insertBefore(element1, element2)
  } else {
    element1.replaceWith(element2)
    parent.insertBefore(element1, afterNode2)
  }
  return true
}

const __moveVertically = (selector, directionTypeName) => {
  return __moveElementVertically(document.querySelector(selector), directionTypeName)
}

const __moveElementVertically = (element, directionTypeName) => {
  if (element == null) {
    return false
  }
  let element2 = directionTypeName == 'UP' ? element.previousElementSibling : element.nextElementSibling
  if (element2 == null) {
    return false
  }
  return __swapElements(element, element2)
}

const __moveAllVertically = (selector, directionTypeName) => {
  let elements = document.querySelectorAll(selector)
  for (i = 0; i < elements.length; ++i) {
    result = __moveElementVertically(elements[i], directionTypeName)
    if (result == false) {
      return false
    }
  }
  return true
}

const __elementsToToggleForButton = (button) => {
  let ticket = button.closest('div.ticket')
  let childrenToNotHide = Array.from(ticket.querySelectorAll('h2.remarkup-header:first-of-type, h3.remarkup-header:first-of-type, button.toggle_ticket, div.ticket_users'))
  let childrenToToggle = [...Array.from(ticket.children)].filter(e => !Array.from(childrenToNotHide).includes(e))
  return childrenToToggle
}

const __expandOrCollapseTicketForButton = (button, expandOrCollapse) => {
  button.classList.add(expandOrCollapse == 'collapse' ? 'collapsed' : 'expanded')
  button.classList.remove(expandOrCollapse == 'collapse' ? 'expanded' : 'collapsed')
  let childrenToToggle = __elementsToToggleForButton(button)
  childrenToToggle.forEach(child => {
    if (expandOrCollapse == 'collapse') {
      child.classList.add('toggle_hidden')
    } else {
      child.classList.remove('toggle_hidden')
    }
  })
}

const __toggleCollapseExpandButton = (button) => {
  if (button.classList.contains('collapsed')) {
    __expandOrCollapseTicketForButton(button, 'expand')
  } else {
    __expandOrCollapseTicketForButton(button, 'collapse')
  }
}

const __expandAllTicketButtons = () => {
  document.querySelectorAll('button.toggle_ticket').forEach(button => __expandOrCollapseTicketForButton(button, 'expand'))
}

const __toggleAllTicketButtons = () => {
  document.querySelectorAll('button.toggle_ticket').forEach(button => __toggleCollapseExpandButton(button))
}

const __collapseAllTicketButtons = () => {
  document.querySelectorAll('button.toggle_ticket').forEach(button => __expandOrCollapseTicketForButton(button, 'collapse'))
}

const __showToggleAllTicketsContainer = () => {
  document.querySelector('div.toggle_all_tickets_container').style.display = 'block'
}

const __hideToggleAllTicketsContainer = () => {
  document.querySelector('div.toggle_all_tickets_container').style.display = 'none'
  return true
}

const __deleteProjectTickets = projectPHID => {
  document.querySelector(`div#_${projectPHID}.project_columns`).remove()
  return true
}

const __hideToggleAllTicketsContainerIfNoSourceProjects = () => {
  if (document.querySelectorAll('div.project_columns').length == 0) {
    __hideToggleAllTicketsContainer()
  }
  return true
}

const __selectConfigurationProjectColumns = (selector, columnsSelectionTypeName) => {
  const buttons = document.querySelectorAll(`${selector} > buttonmenu > button`)
  const buttonsToClick = Array.from(buttons).filter(button => {
    return ((columnsSelectionTypeName == 'NONE' && button.classList.contains('selected')) || (columnsSelectionTypeName == 'ALL' && !button.classList.contains('selected')))
  })
  buttonsToClick.forEach(button => button.click())
  return true
}

const __selectedTicketClassName = 'selected_ticket'

const __clamp = (num, min, max) => Math.min(Math.max(num, min), max)

const __firstOnscreenTicket = () => {
  const insetTop = 300
  return Array.from(document.querySelectorAll('div.ticket')).find((e, i, a) => {
    const rect = e.getBoundingClientRect()
    return (rect.top > insetTop || rect.top + rect.height > insetTop)
  })
}

const __deselectTicket = () => {
  Array.from(document.querySelectorAll(`.${__selectedTicketClassName}`)).forEach(ticket => ticket.classList.remove(__selectedTicketClassName))
}

const __ticketToSelectAndScrollToInDirection = (selector, goForward, previouslySelectedTicket) => {
  const tickets = Array.from(document.querySelectorAll(selector))
  let index = 0
  const offset = goForward ? 1 : -1
  for (i = 0; i < tickets.length; i++) {
    const ticket = tickets[i]
    if (ticket === previouslySelectedTicket) {
      index = __clamp(i + offset, 0, tickets.length - 1)
      break
    }
  }
  return tickets[index]
}

const __toggleSelectedTicket = event => {
  const selectedTicket = document.querySelector(`.${__selectedTicketClassName}`)
  if (selectedTicket == null || (event.code != 'ArrowLeft' && event.code != 'ArrowRight')) {
    return false
  }
  const button = selectedTicket.querySelector('button.toggle_ticket')
  if (button == null) {
    return false
  }
  __expandOrCollapseTicketForButton(button, event.code == 'ArrowLeft' ? 'collapse' : 'expand')
  __debouncedDeselectTicket()
  return true
}

const __dispatchShiftArrowEvents = event => {
  if (!__isShiftArrowEvent(event)) {
    return
  }
  if (__toggleSelectedTicket(event)) {
    return
  }
  __selectAndScrollToNextOrPreviousOnscreenTicket(event)
}

const __selectAndScrollToNextOrPreviousOnscreenTicket = event => {
  if (!__isShiftArrowEvent(event)) {
    return
  }
  const previouslySelectedTicket = document.querySelector(`.${__selectedTicketClassName}`)
  const ticketToSelect = (previouslySelectedTicket == null) ? __firstOnscreenTicket() : __ticketToSelectAndScrollToInDirection('div.ticket', event.code == 'ArrowDown', previouslySelectedTicket)
  if (ticketToSelect == null) {
    return
  }
  __deselectTicket()
  ticketToSelect.classList.add(__selectedTicketClassName)
  ticketToSelect.scrollIntoView(true)
  // scroll down a bit here?
  window.scrollBy(0, -21)
  event.stopPropagation()
  event.preventDefault()
}

const debounce = (func, timeout = 300) => {
  let timer
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => { func.apply(this, args) }, timeout)
  }
}

const __debouncedDeselectTicket = debounce(() => {
  __deselectTicket()
}, 3000)

const __isShiftArrowEvent = event => {
  return (event.shiftKey == true && (event.code == 'ArrowDown' || event.code == 'ArrowUp' || event.code == 'ArrowLeft' || event.code == 'ArrowRight'))
}

const __preventBeepOnShiftUpAndDownArrowEvents = event => {
  if (!__isShiftArrowEvent(event)) {
    return
  }
  event.stopPropagation()
  event.preventDefault()
}

document.addEventListener('click', __deselectTicket)
document.addEventListener('scroll', __debouncedDeselectTicket)
document.addEventListener('keyup', __dispatchShiftArrowEvents)
document.addEventListener('keydown', __preventBeepOnShiftUpAndDownArrowEvents)
