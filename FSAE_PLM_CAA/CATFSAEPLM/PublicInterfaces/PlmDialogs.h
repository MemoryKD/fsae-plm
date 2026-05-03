#ifndef PlmDialogs_H
#define PlmDialogs_H

#include "CATDlgDialog.h"
#include "CATDlgEditor.h"
#include "CATDlgPushButton.h"
#include "CATDlgLabel.h"
#include "CATUnicodeString.h"

class PlmBridge;

/**
 * Login Dialog - server URL, username, password
 */
class PlmLoginDialog : public CATDlgDialog
{
    CATDeclareClass;

public:
    PlmLoginDialog(PlmBridge* bridge);
    virtual ~PlmLoginDialog();

private:
    PlmBridge* _bridge;
    CATDlgEditor* _serverEditor;
    CATDlgEditor* _usernameEditor;
    CATDlgEditor* _passwordEditor;
    CATDlgLabel* _statusLabel;
    CATDlgPushButton* _loginBtn;
    CATDlgPushButton* _cancelBtn;

    void OnLogin(CATCommand* cmd, CATNotification* evt, void* data);
    void OnCancel(CATCommand* cmd, CATNotification* evt, void* data);
};

/**
 * Parts List Dialog - search + DataGridView-like list
 */
class PlmPartsListDialog : public CATDlgDialog
{
    CATDeclareClass;

public:
    PlmPartsListDialog(PlmBridge* bridge);
    virtual ~PlmPartsListDialog();

    // Returns the selected part ID after dialog closes
    const char* GetSelectedPartId() const;

private:
    PlmBridge* _bridge;
    CATDlgEditor* _searchEditor;
    CATDlgPushButton* _searchBtn;
    CATDlgPushButton* _refreshBtn;
    CATDlgListBrowser* _partsList;
    CATDlgPushButton* _detailBtn;
    CATDlgPushButton* _closeBtn;
    char _selectedPartId[64];

    void OnSearch(CATCommand* cmd, CATNotification* evt, void* data);
    void OnDetail(CATCommand* cmd, CATNotification* evt, void* data);
    void OnClose(CATCommand* cmd, CATNotification* evt, void* data);
    void LoadParts(const char* search);
};

/**
 * Part Detail Dialog - info, versions, BOM, action buttons
 */
class PlmPartDetailDialog : public CATDlgDialog
{
    CATDeclareClass;

public:
    PlmPartDetailDialog(PlmBridge* bridge, const char* partId);
    virtual ~PlmPartDetailDialog();

    // Results accessible after dialog closes
    const char* GetCheckoutFilePath() const;
    bool WasCheckedIn() const;
    bool WasPublished() const;

private:
    PlmBridge* _bridge;
    char _partId[64];
    char _checkoutPath[512];
    bool _checkedIn;
    bool _published;

    CATDlgLabel* _infoLabels[8];  // PartNumber, Name, Type, etc.
    CATDlgListBrowser* _versionList;
    CATDlgListBrowser* _bomList;
    CATDlgPushButton* _checkoutBtn;
    CATDlgPushButton* _checkinBtn;
    CATDlgPushButton* _publishBtn;
    CATDlgPushButton* _syncBtn;
    CATDlgPushButton* _closeBtn;

    void LoadPartInfo();
    void LoadVersions();
    void LoadBom();
    void OnCheckout(CATCommand* cmd, CATNotification* evt, void* data);
    void OnCheckin(CATCommand* cmd, CATNotification* evt, void* data);
    void OnPublish(CATCommand* cmd, CATNotification* evt, void* data);
    void OnSync(CATCommand* cmd, CATNotification* evt, void* data);
    void OnClose(CATCommand* cmd, CATNotification* evt, void* data);
};

/**
 * Create Part Dialog - template, subsystem, type, name
 */
class PlmCreatePartDialog : public CATDlgDialog
{
    CATDeclareClass;

public:
    PlmCreatePartDialog(PlmBridge* bridge);
    virtual ~PlmCreatePartDialog();

    const char* GetCreatedPartId() const;
    const char* GetCreatedPartNumber() const;

private:
    PlmBridge* _bridge;
    CATDlgEditor* _nameEditor;
    CATDlgCombo* _typeCombo;
    CATDlgCombo* _templateCombo;
    CATDlgCombo* _subsystemCombo;
    CATDlgLabel* _previewLabel;
    CATDlgPushButton* _createBtn;
    CATDlgPushButton* _cancelBtn;
    char _createdPartId[64];
    char _createdPartNumber[128];

    void OnTemplateChanged(CATCommand* cmd, CATNotification* evt, void* data);
    void OnCreate(CATCommand* cmd, CATNotification* evt, void* data);
    void OnCancel(CATCommand* cmd, CATNotification* evt, void* data);
    void UpdatePreview();
};

#endif
