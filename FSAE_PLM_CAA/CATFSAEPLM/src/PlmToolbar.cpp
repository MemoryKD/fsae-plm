/**
 * PlmToolbar.cpp - FSAE-PLM Workbench and Toolbar creation.
 *
 * Creates a custom workbench in CATIA V5 with a toolbar containing
 * buttons for all PLM operations.
 */
#include "PlmToolbar.h"
#include "PlmCommands.h"
#include "PlmBridge.h"

// CATIA V5 headers
#include "CATCommandHeader.h"
#include "CATCmdContainer.h"
#include "CATCreateWorkbench.h"
#include "CATFrmWorkbench.h"

// Global PLM bridge instance (shared across all commands)
static PlmBridge* g_plmBridge = nullptr;

PlmBridge* GetPlmBridge()
{
    if (!g_plmBridge) g_plmBridge = new PlmBridge();
    return g_plmBridge;
}

// ============================================================
// PlmWorkbench
// ============================================================
CATImplementClass(PlmWorkbench, Implementation, CATWorkbench, CATBaseUnknown);

PlmWorkbench::PlmWorkbench()
    : CATWorkbench("FSAE-PLM", "FSAE-PLM")
{
}

PlmWorkbench::~PlmWorkbench()
{
}

CATCmdContainer* PlmWorkbench::CreateCommands()
{
    // Create the toolbar container
    CATCmdContainer* toolbar = new CATCmdContainer("FSAE-PLM Toolbar", "FSAE-PLM");
    if (!toolbar) return NULL;

    // Create command headers for each toolbar button
    PlmBridge* bridge = GetPlmBridge();

    // Login button
    CATCommandHeader* loginHeader = new CATCommandHeader(
        "PlmLoginCmd",
        "PLM Login",
        "",
        NULL,
        (CATCommandMethod)&PlmLoginCommand::Activate,
        bridge
    );
    toolbar->AddChild(loginHeader);

    // Search Parts button
    CATCommandHeader* searchHeader = new CATCommandHeader(
        "PlmSearchCmd",
        "PLM Search",
        "",
        NULL,
        (CATCommandMethod)&PlmSearchCommand::Activate,
        bridge
    );
    toolbar->AddChild(searchHeader);

    // Checkout button
    CATCommandHeader* checkoutHeader = new CATCommandHeader(
        "PlmCheckoutCmd",
        "PLM Checkout",
        "",
        NULL,
        (CATCommandMethod)&PlmCheckoutCommand::Activate,
        bridge
    );
    toolbar->AddChild(checkoutHeader);

    // Checkin button
    CATCommandHeader* checkinHeader = new CATCommandHeader(
        "PlmCheckinCmd",
        "PLM Checkin",
        "",
        NULL,
        (CATCommandMethod)&PlmCheckinCommand::Activate,
        bridge
    );
    toolbar->AddChild(checkinHeader);

    // Publish button
    CATCommandHeader* publishHeader = new CATCommandHeader(
        "PlmPublishCmd",
        "PLM Publish",
        "",
        NULL,
        (CATCommandMethod)&PlmPublishCommand::Activate,
        bridge
    );
    toolbar->AddChild(publishHeader);

    // Sync Properties button
    CATCommandHeader* syncHeader = new CATCommandHeader(
        "PlmSyncCmd",
        "PLM Sync",
        "",
        NULL,
        (CATCommandMethod)&PlmSyncCommand::Activate,
        bridge
    );
    toolbar->AddChild(syncHeader);

    // Create Part button
    CATCommandHeader* createHeader = new CATCommandHeader(
        "PlmCreatePartCmd",
        "PLM Create Part",
        "",
        NULL,
        (CATCommandMethod)&PlmCreatePartCommand::Activate,
        bridge
    );
    toolbar->AddChild(createHeader);

    return toolbar;
}

// ============================================================
// Workbench factory registration
// ============================================================
CATImplementClass(PlmWorkbenchAddin, DataExtension, CATFrmWorkbench, CATBaseUnknown);

PlmWorkbenchAddin::PlmWorkbenchAddin()
{
}

PlmWorkbenchAddin::~PlmWorkbenchAddin()
{
}

CATCmdContainer* PlmWorkbenchAddin::CreateToolbar()
{
    PlmWorkbench wb;
    return wb.CreateCommands();
}
