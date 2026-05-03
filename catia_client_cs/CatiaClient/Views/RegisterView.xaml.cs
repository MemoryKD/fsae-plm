using System.Windows.Controls;
using CatiaClient.ViewModels;

namespace CatiaClient.Views;

public partial class RegisterView : UserControl
{
    public RegisterView()
    {
        InitializeComponent();
        PasswordBox.PasswordChanged += (s, e) =>
        {
            if (DataContext is RegisterViewModel vm)
                vm.Password = PasswordBox.Password;
        };
    }
}
