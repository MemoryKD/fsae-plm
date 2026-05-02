using System.Windows;
using System.Windows.Controls;
using CatiaClient.Models;
using CatiaClient.ViewModels;

namespace CatiaClient.Views;

public partial class PartsView : UserControl
{
    public PartsView()
    {
        InitializeComponent();
    }

    private void PartsList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (e.AddedItems.Count > 0 && DataContext is PartsViewModel vm && e.AddedItems[0] is Part part)
        {
            vm.SelectPart(part);
        }
    }
}
