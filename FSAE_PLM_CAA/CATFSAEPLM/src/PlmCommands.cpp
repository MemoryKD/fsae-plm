/**
 * PlmCommands.cpp - CAA V5 Command implementations for PLM toolbar buttons.
 *
 * Each command's Activate() method is called when the user clicks the
 * corresponding toolbar button. Commands create dialogs or perform
 * direct API operations.
 */
#include "PlmCommands.h"
#include "PlmDialogs.h"
#include "PlmBridge.h"

// CATIA V5 headers
#include "CATApplicationFrame.h"
#include "CATPathElement.h"
#include "CATDocument.h"
#include "CATIProduct.h"
#include "CATIDocRoots.h"
#include "CATFrmEditor.h"

// ============================================================
// PlmBaseCommand
// ============================================================
CATImplementClass(PlmBaseCommand, Implementation, CATCommand, CATBaseUnknown);

PlmBaseCommand::PlmBaseCommand(const CATString& commandId, PlmBridge* bridge)
    : CATCommand(commandId), _bridge(bridge)
{
}

PlmBaseCommand::~PlmBaseCommand()
{
}

// ============================================================
// PlmLoginCommand
// ============================================================
CATImplementClass(PlmLoginCommand, Implementation, PlmBaseCommand, CATBaseUnknown);

PlmLoginCommand::PlmLoginCommand(PlmBridge* bridge)
    : PlmBaseCommand("PlmLogin", bridge)
{
}

PlmLoginCommand::~PlmLoginCommand()
{
}

void PlmLoginCommand::Activate(CATCommand* iFromClient, CATNotification* iNotification)
{
    if (!_bridge) return;

    PlmLoginDialog* dlg = new PlmLoginDialog(_bridge);
    dlg->SetVisibility(CATDlgShow);
    dlg->CenterOnScreen();
}

// ============================================================
// PlmSearchCommand
// ============================================================
CATImplementClass(PlmSearchCommand, Implementation, PlmBaseCommand, CATBaseUnknown);

PlmSearchCommand::PlmSearchCommand(PlmBridge* bridge)
    : PlmBaseCommand("PlmSearch", bridge)
{
}

PlmSearchCommand::~PlmSearchCommand()
{
}

void PlmSearchCommand::Activate(CATCommand* iFromClient, CATNotification* iNotification)
{
    if (!_bridge || !_bridge->IsLoggedIn()) return;

    PlmPartsListDialog* dlg = new PlmPartsListDialog(_bridge);
    dlg->SetVisibility(CATDlgShow);
    dlg->CenterOnScreen();
}

// ============================================================
// PlmCheckoutCommand
// ============================================================
CATImplementClass(PlmCheckoutCommand, Implementation, PlmBaseCommand, CATBaseUnknown);

PlmCheckoutCommand::PlmCheckoutCommand(PlmBridge* bridge)
    : PlmBaseCommand("PlmCheckout", bridge)
{
}

PlmCheckoutCommand::~PlmCheckoutCommand()
{
}

void PlmCheckoutCommand::Activate(CATCommand* iFromClient, CATNotification* iNotification)
{
    if (!_bridge || !_bridge->IsLoggedIn()) return;

    // Get current document's PLM part ID from UserProperties
    // TODO: Read PLM_PartNumber from active document's UserRefProperties
    // Look up part by number via API, then checkout and download

    // For now, show parts list for user to select
    PlmPartsListDialog* listDlg = new PlmPartsListDialog(_bridge);
    listDlg->SetVisibility(CATDlgShow);
    listDlg->CenterOnScreen();
    // After user selects a part, PlmPartDetailDialog handles checkout
}

// ============================================================
// PlmCheckinCommand
// ============================================================
CATImplementClass(PlmCheckinCommand, Implementation, PlmBaseCommand, CATBaseUnknown);

PlmCheckinCommand::PlmCheckinCommand(PlmBridge* bridge)
    : PlmBaseCommand("PlmCheckin", bridge)
{
}

PlmCheckinCommand::~PlmCheckinCommand()
{
}

void PlmCheckinCommand::Activate(CATCommand* iFromClient, CATNotification* iNotification)
{
    if (!_bridge || !_bridge->IsLoggedIn()) return;

    // Get active document path
    CATFrmEditor* editor = CATFrmEditor::GetCurrentEditor();
    if (!editor) return;

    CATDocument* doc = editor->GetDocument();
    if (!doc) return;

    CATUnicodeString docPath;
    doc->GetDocStorageName(docPath);

    // Get part ID from UserProperties
    // TODO: Read PLM_PartNumber and look up by API

    // Call Checkin API with the document path
    PlmBridge::PartInfo updatedPart;
    // _bridge->Checkin(partId, docPath.ConvertToChar(), updatedPart);
}

// ============================================================
// PlmPublishCommand
// ============================================================
CATImplementClass(PlmPublishCommand, Implementation, PlmBaseCommand, CATBaseUnknown);

PlmPublishCommand::PlmPublishCommand(PlmBridge* bridge)
    : PlmBaseCommand("PlmPublish", bridge)
{
}

PlmPublishCommand::~PlmPublishCommand()
{
}

void PlmPublishCommand::Activate(CATCommand* iFromClient, CATNotification* iNotification)
{
    if (!_bridge || !_bridge->IsLoggedIn()) return;

    // TODO: Get part ID from current document, confirm with user, call Publish API
}

// ============================================================
// PlmSyncCommand
// ============================================================
CATImplementClass(PlmSyncCommand, Implementation, PlmBaseCommand, CATBaseUnknown);

PlmSyncCommand::PlmSyncCommand(PlmBridge* bridge)
    : PlmBaseCommand("PlmSync", bridge)
{
}

PlmSyncCommand::~PlmSyncCommand()
{
}

void PlmSyncCommand::Activate(CATCommand* iFromClient, CATNotification* iNotification)
{
    if (!_bridge || !_bridge->IsLoggedIn()) return;

    // TODO:
    // 1. Get part ID from current document's UserProperties
    // 2. Fetch current part info from API
    // 3. Write PLM_PartNumber, PLM_Name, PLM_Version, PLM_State
    //    to document's UserRefProperties
}

// ============================================================
// PlmCreatePartCommand
// ============================================================
CATImplementClass(PlmCreatePartCommand, Implementation, PlmBaseCommand, CATBaseUnknown);

PlmCreatePartCommand::PlmCreatePartCommand(PlmBridge* bridge)
    : PlmBaseCommand("PlmCreatePart", bridge)
{
}

PlmCreatePartCommand::~PlmCreatePartCommand()
{
}

void PlmCreatePartCommand::Activate(CATCommand* iFromClient, CATNotification* iNotification)
{
    if (!_bridge || !_bridge->IsLoggedIn()) return;

    PlmCreatePartDialog* dlg = new PlmCreatePartDialog(_bridge);
    dlg->SetVisibility(CATDlgShow);
    dlg->CenterOnScreen();
}
