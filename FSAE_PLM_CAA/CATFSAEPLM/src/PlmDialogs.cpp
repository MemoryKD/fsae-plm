/**
 * PlmDialogs.cpp - CATIA V5 native dialogs for PLM operations.
 *
 * Uses CATDlgDialog, CATDlgEditor, CATDlgPushButton, CATDlgListBrowser
 * for CATIA-native UI that matches the CATIA look and feel.
 */
#include "PlmDialogs.h"
#include "PlmBridge.h"

// CATIA V5 dialog headers
#include "CATDlgGridLayout.h"
#include "CATDlgBoxLayout.h"
#include "CATDlgSeparator.h"
#include "CATDlgCombo.h"
#include "CATMessage.h"

// ============================================================
// PlmLoginDialog
// ============================================================
CATImplementClass(PlmLoginDialog, Implementation, CATDlgDialog, CATBaseUnknown);

PlmLoginDialog::PlmLoginDialog(PlmBridge* bridge)
    : CATDlgDialog(NULL, "FSAE-PLM Login", CATDlgWndModal),
      _bridge(bridge)
{
    // Layout
    CATDlgGridLayout* grid = new CATDlgGridLayout(this, 2);

    // Server URL
    new CATDlgLabel(this, "Server:");
    _serverEditor = new CATDlgEditor(this, "");
    _serverEditor->SetVisibleTextWidth(30);
    if (_bridge) _serverEditor->SetText(_bridge->GetServerUrl());

    // Username
    new CATDlgLabel(this, "Username:");
    _usernameEditor = new CATDlgEditor(this, "");

    // Password
    new CATDlgLabel(this, "Password:");
    _passwordEditor = new CATDlgEditor(this, "");
    _passwordEditor->SetPasswordMode(TRUE);

    // Status label
    _statusLabel = new CATDlgLabel(this, "");
    _statusLabel->SetGridRowSpan(2);

    // Buttons
    CATDlgBoxLayout* btnBox = new CATDlgBoxLayout(this, CATDlgBoxLayoutHorizontal);
    _loginBtn = new CATDlgPushButton(this, "Login");
    _cancelBtn = new CATDlgPushButton(this, "Cancel");

    // Callbacks
    AddAnalyseNotificationCB(_loginBtn, _loginBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmLoginDialog::OnLogin, NULL);
    AddAnalyseNotificationCB(_cancelBtn, _cancelBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmLoginDialog::OnCancel, NULL);
}

PlmLoginDialog::~PlmLoginDialog()
{
}

void PlmLoginDialog::OnLogin(CATCommand* cmd, CATNotification* evt, void* data)
{
    if (!_bridge) return;

    CATUnicodeString server = _serverEditor->GetText();
    CATUnicodeString username = _usernameEditor->GetText();
    CATUnicodeString password = _passwordEditor->GetText();

    _bridge->SetServerUrl(server.ConvertToChar());

    if (_bridge->Login(username.ConvertToChar(), password.ConvertToChar()))
    {
        _statusLabel->SetText("Login successful");
        RequestDelayedDestruction();
    }
    else
    {
        _statusLabel->SetText(_bridge->GetLastError());
    }
}

void PlmLoginDialog::OnCancel(CATCommand* cmd, CATNotification* evt, void* data)
{
    RequestDelayedDestruction();
}

// ============================================================
// PlmPartsListDialog
// ============================================================
CATImplementClass(PlmPartsListDialog, Implementation, CATDlgDialog, CATBaseUnknown);

PlmPartsListDialog::PlmPartsListDialog(PlmBridge* bridge)
    : CATDlgDialog(NULL, "FSAE-PLM Parts", CATDlgWndModal),
      _bridge(bridge)
{
    memset(_selectedPartId, 0, sizeof(_selectedPartId));

    // Search bar
    CATDlgBoxLayout* searchBox = new CATDlgBoxLayout(this, CATDlgBoxLayoutHorizontal);
    _searchEditor = new CATDlgEditor(this, "");
    _searchEditor->SetVisibleTextWidth(25);
    _searchBtn = new CATDlgPushButton(this, "Search");
    _refreshBtn = new CATDlgPushButton(this, "Refresh");

    // Parts list (CATDlgListBrowser)
    _partsList = new CATDlgListBrowser(this, "");
    _partsList->SetColumnHeaders("Part Number;Name;Type;Version;State;Check State;Branch");
    _partsList->SetColumnWidths("120;180;60;50;70;70;80");

    // Action buttons
    CATDlgBoxLayout* btnBox = new CATDlgBoxLayout(this, CATDlgBoxLayoutHorizontal);
    _detailBtn = new CATDlgPushButton(this, "View Detail");
    _closeBtn = new CATDlgPushButton(this, "Close");

    // Callbacks
    AddAnalyseNotificationCB(_searchBtn, _searchBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmPartsListDialog::OnSearch, NULL);
    AddAnalyseNotificationCB(_detailBtn, _detailBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmPartsListDialog::OnDetail, NULL);
    AddAnalyseNotificationCB(_closeBtn, _closeBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmPartsListDialog::OnClose, NULL);

    // Auto-load parts on open
    LoadParts("");
}

PlmPartsListDialog::~PlmPartsListDialog()
{
}

const char* PlmPartsListDialog::GetSelectedPartId() const { return _selectedPartId; }

void PlmPartsListDialog::LoadParts(const char* search)
{
    if (!_bridge) return;

    _partsList->ClearLine();

    PlmBridge::PartInfo parts[100];
    int count = _bridge->GetParts(search, parts, 100);

    for (int i = 0; i < count; i++)
    {
        char line[512];
        sprintf_s(line, "%s;%s;%s;%s;%s;%s;%s",
                  parts[i].partNumber, parts[i].name, parts[i].type,
                  parts[i].currentVersion, parts[i].lifecycleState,
                  parts[i].checkState, parts[i].branchName);
        _partsList->SetLineItem(i, line);
        _partsList->SetLineData(i, (void*)strdup(parts[i].id));
    }
}

void PlmPartsListDialog::OnSearch(CATCommand* cmd, CATNotification* evt, void* data)
{
    CATUnicodeString searchText = _searchEditor->GetText();
    LoadParts(searchText.ConvertToChar());
}

void PlmPartsListDialog::OnDetail(CATCommand* cmd, CATNotification* evt, void* data)
{
    int selIndex = _partsList->GetSelectIndex();
    if (selIndex < 0) return;

    char* partId = (char*)_partsList->GetLineData(selIndex);
    if (!partId) return;

    strncpy_s(_selectedPartId, partId, sizeof(_selectedPartId) - 1);

    // Open part detail dialog
    PlmPartDetailDialog* detailDlg = new PlmPartDetailDialog(_bridge, _selectedPartId);
    detailDlg->SetVisibility(CATDlgShow);
    detailDlg->CenterOnScreen();
}

void PlmPartsListDialog::OnClose(CATCommand* cmd, CATNotification* evt, void* data)
{
    RequestDelayedDestruction();
}

// ============================================================
// PlmPartDetailDialog
// ============================================================
CATImplementClass(PlmPartDetailDialog, Implementation, CATDlgDialog, CATBaseUnknown);

PlmPartDetailDialog::PlmPartDetailDialog(PlmBridge* bridge, const char* partId)
    : CATDlgDialog(NULL, "Part Detail", CATDlgWndModal),
      _bridge(bridge), _checkedIn(false), _published(false)
{
    strncpy_s(_partId, partId, sizeof(_partId) - 1);
    memset(_checkoutPath, 0, sizeof(_checkoutPath));

    // Info section
    for (int i = 0; i < 8; i++)
        _infoLabels[i] = new CATDlgLabel(this, "");

    // Version history
    _versionList = new CATDlgListBrowser(this, "Version History");
    _versionList->SetColumnHeaders("Version;Type;Size;Comment;Date");

    // BOM
    _bomList = new CATDlgListBrowser(this, "BOM");
    _bomList->SetColumnHeaders("Part ID;Quantity;Level");

    // Action buttons
    CATDlgBoxLayout* btnBox = new CATDlgBoxLayout(this, CATDlgBoxLayoutHorizontal);
    _checkoutBtn = new CATDlgPushButton(this, "Checkout");
    _checkinBtn = new CATDlgPushButton(this, "Checkin");
    _publishBtn = new CATDlgPushButton(this, "Publish");
    _syncBtn = new CATDlgPushButton(this, "Sync Props");
    _closeBtn = new CATDlgPushButton(this, "Close");

    // Callbacks
    AddAnalyseNotificationCB(_checkoutBtn, _checkoutBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmPartDetailDialog::OnCheckout, NULL);
    AddAnalyseNotificationCB(_checkinBtn, _checkinBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmPartDetailDialog::OnCheckin, NULL);
    AddAnalyseNotificationCB(_publishBtn, _publishBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmPartDetailDialog::OnPublish, NULL);
    AddAnalyseNotificationCB(_syncBtn, _syncBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmPartDetailDialog::OnSync, NULL);
    AddAnalyseNotificationCB(_closeBtn, _closeBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmPartDetailDialog::OnClose, NULL);

    LoadPartInfo();
    LoadVersions();
    LoadBom();
}

PlmPartDetailDialog::~PlmPartDetailDialog()
{
}

const char* PlmPartDetailDialog::GetCheckoutFilePath() const { return _checkoutPath; }
bool PlmPartDetailDialog::WasCheckedIn() const { return _checkedIn; }
bool PlmPartDetailDialog::WasPublished() const { return _published; }

void PlmPartDetailDialog::LoadPartInfo()
{
    if (!_bridge) return;

    PlmBridge::PartInfo part;
    if (_bridge->GetPart(_partId, part))
    {
        char labels[8][256];
        sprintf_s(labels[0], "Part Number: %s", part.partNumber);
        sprintf_s(labels[1], "Name: %s", part.name);
        sprintf_s(labels[2], "Type: %s", part.type);
        sprintf_s(labels[3], "Subsystem: %s", part.subsystem);
        sprintf_s(labels[4], "Version: %s", part.currentVersion);
        sprintf_s(labels[5], "Lifecycle: %s", part.lifecycleState);
        sprintf_s(labels[6], "Check State: %s", part.checkState);
        sprintf_s(labels[7], "Branch: %s", part.branchName);

        for (int i = 0; i < 8; i++)
            _infoLabels[i]->SetText(labels[i]);

        // Enable/disable buttons based on state
        bool isCheckedIn = (strcmp(part.checkState, "Checked In") == 0);
        bool isPublished = (strcmp(part.lifecycleState, "Published") == 0);

        _checkoutBtn->SetEnabled(isCheckedIn && !isPublished);
        _checkinBtn->SetEnabled(!isCheckedIn);
        _publishBtn->SetEnabled(isCheckedIn && !isPublished);
    }
}

void PlmPartDetailDialog::LoadVersions()
{
    if (!_bridge) return;

    _versionList->ClearLine();

    PlmBridge::VersionInfo versions[50];
    int count = _bridge->GetVersions(_partId, versions, 50);

    for (int i = 0; i < count; i++)
    {
        char line[512];
        sprintf_s(line, "%s;%s;%d;%s;%s",
                  versions[i].versionNumber, versions[i].fileType,
                  versions[i].fileSize, versions[i].comment, versions[i].createdAt);
        _versionList->SetLineItem(i, line);
    }
}

void PlmPartDetailDialog::LoadBom()
{
    // TODO: Call GetBom API and populate _bomList
}

void PlmPartDetailDialog::OnCheckout(CATCommand* cmd, CATNotification* evt, void* data)
{
    if (!_bridge) return;

    PlmBridge::PartInfo updatedPart;
    if (_bridge->Checkout(_partId, updatedPart))
    {
        // Download latest version
        PlmBridge::VersionInfo versions[1];
        if (_bridge->GetVersions(_partId, versions, 1) > 0)
        {
            char savePath[512];
            sprintf_s(savePath, "%s\\catia_plm\\%s_%s.%s",
                      getenv("TEMP"), updatedPart.partNumber,
                      versions[0].versionNumber, versions[0].fileType);
            CreateDirectoryA(savePath, NULL); // Ensure dir exists

            // Recompute path without trailing dir separator issue
            char filePath[512];
            sprintf_s(filePath, "%s\\catia_plm\\%s_%s.%s",
                      getenv("TEMP"), updatedPart.partNumber,
                      versions[0].versionNumber, versions[0].fileType);

            if (_bridge->DownloadVersion(_partId, versions[0].id, filePath))
            {
                strncpy_s(_checkoutPath, filePath, sizeof(_checkoutPath) - 1);
                _infoLabels[6]->SetText("Check State: Checked Out");
                _checkoutBtn->SetEnabled(false);
                _checkinBtn->SetEnabled(true);
            }
        }
    }
}

void PlmPartDetailDialog::OnCheckin(CATCommand* cmd, CATNotification* evt, void* data)
{
    if (!_bridge) return;

    // The VBS macro will pass the file path
    // For now, use the checkout path
    if (_checkoutPath[0])
    {
        PlmBridge::PartInfo updatedPart;
        if (_bridge->Checkin(_partId, _checkoutPath, updatedPart))
        {
            _checkedIn = true;
            _infoLabels[6]->SetText("Check State: Checked In");
            _checkinBtn->SetEnabled(false);
            _checkoutBtn->SetEnabled(true);
            LoadPartInfo();
            LoadVersions();
        }
    }
}

void PlmPartDetailDialog::OnPublish(CATCommand* cmd, CATNotification* evt, void* data)
{
    if (!_bridge) return;

    PlmBridge::PartInfo updatedPart;
    if (_bridge->Publish(_partId, updatedPart))
    {
        _published = true;
        _infoLabels[5]->SetText("Lifecycle: Published");
        _publishBtn->SetEnabled(false);
        _checkoutBtn->SetEnabled(false);
    }
}

void PlmPartDetailDialog::OnSync(CATCommand* cmd, CATNotification* evt, void* data)
{
    // TODO: Fetch part info and write to CATIA document UserRefProperties
}

void PlmPartDetailDialog::OnClose(CATCommand* cmd, CATNotification* evt, void* data)
{
    RequestDelayedDestruction();
}

// ============================================================
// PlmCreatePartDialog
// ============================================================
CATImplementClass(PlmCreatePartDialog, Implementation, CATDlgDialog, CATBaseUnknown);

PlmCreatePartDialog::PlmCreatePartDialog(PlmBridge* bridge)
    : CATDlgDialog(NULL, "Create Part", CATDlgWndModal),
      _bridge(bridge)
{
    memset(_createdPartId, 0, sizeof(_createdPartId));
    memset(_createdPartNumber, 0, sizeof(_createdPartNumber));

    // Name
    new CATDlgLabel(this, "Part Name:");
    _nameEditor = new CATDlgEditor(this, "");

    // Type
    new CATDlgLabel(this, "Type:");
    _typeCombo = new CATDlgCombo(this, CATDlgComboDropDown);
    _typeCombo->SetLine("part");
    _typeCombo->SetLine("assembly");
    _typeCombo->SetLine("document");

    // Template
    new CATDlgLabel(this, "Template:");
    _templateCombo = new CATDlgCombo(this, CATDlgComboDropDown);
    // Templates loaded from API

    // Subsystem
    new CATDlgLabel(this, "Subsystem:");
    _subsystemCombo = new CATDlgCombo(this, CATDlgComboDropDown);

    // Preview
    _previewLabel = new CATDlgLabel(this, "Part Number: (select template)");

    // Buttons
    CATDlgBoxLayout* btnBox = new CATDlgBoxLayout(this, CATDlgBoxLayoutHorizontal);
    _createBtn = new CATDlgPushButton(this, "Create");
    _cancelBtn = new CATDlgPushButton(this, "Cancel");

    // Load templates
    if (_bridge)
    {
        PlmBridge::TemplateInfo templates[20];
        int count = _bridge->GetTemplates(templates, 20);
        for (int i = 0; i < count; i++)
            _templateCombo->SetLine(templates[i].name);
    }

    // Callbacks
    AddAnalyseNotificationCB(_createBtn, _createBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmCreatePartDialog::OnCreate, NULL);
    AddAnalyseNotificationCB(_cancelBtn, _cancelBtn->GetPushBActivateNotification(),
                              (CATCommandMethod)&PlmCreatePartDialog::OnCancel, NULL);
    AddAnalyseNotificationCB(_templateCombo, _templateCombo->GetComboSelectNotification(),
                              (CATCommandMethod)&PlmCreatePartDialog::OnTemplateChanged, NULL);
}

PlmCreatePartDialog::~PlmCreatePartDialog()
{
}

const char* PlmCreatePartDialog::GetCreatedPartId() const { return _createdPartId; }
const char* PlmCreatePartDialog::GetCreatedPartNumber() const { return _createdPartNumber; }

void PlmCreatePartDialog::OnTemplateChanged(CATCommand* cmd, CATNotification* evt, void* data)
{
    UpdatePreview();
}

void PlmCreatePartDialog::UpdatePreview()
{
    if (!_bridge) return;
    // TODO: Get template ID from selected template name
    // Call GetNextPartNumber and update _previewLabel
}

void PlmCreatePartDialog::OnCreate(CATCommand* cmd, CATNotification* evt, void* data)
{
    if (!_bridge) return;

    CATUnicodeString name = _nameEditor->GetText();
    int typeIndex = _typeCombo->GetSelect();
    int subsystemIndex = _subsystemCombo->GetSelect();

    if (name.GetLengthInChar() == 0) return;

    // Get type and subsystem strings
    CATUnicodeString type = "part";
    CATUnicodeString subsystem = "";
    _typeCombo->GetLine(typeIndex, type);

    PlmBridge::PartInfo newPart;
    // TODO: Get template ID and call CreatePart
    // if (_bridge->CreatePart(name.ConvertToChar(), type.ConvertToChar(),
    //                          subsystem.ConvertToChar(), templateId, newPart))
    // {
    //     strncpy_s(_createdPartId, newPart.id, sizeof(_createdPartId) - 1);
    //     strncpy_s(_createdPartNumber, newPart.partNumber, sizeof(_createdPartNumber) - 1);
    //     RequestDelayedDestruction();
    // }
}

void PlmCreatePartDialog::OnCancel(CATCommand* cmd, CATNotification* evt, void* data)
{
    RequestDelayedDestruction();
}
