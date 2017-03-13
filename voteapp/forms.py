from django import forms

from django.utils.translation import ugettext as _





class WriteInForm(forms.Form):
    write_in_form = forms.CharField(widget=forms.TextInput, required=False, max_length=200,label="Add a write in option")


class MultiVoteForm(forms.Form):

    def __init__(self, *args, **kwargs):

        dynamic_form = kwargs.pop('extra')
        self.form_type = dynamic_form['type']
        self.max_choices = dynamic_form['max_choices']
        super(MultiVoteForm, self).__init__(*args, **kwargs)


        if self.form_type == 'ranked':
            choices = []
            for i in range(1,len(dynamic_form['option_list'])+1):
                choices.append((i,i))
            choices.append(('',''))
            for option in dynamic_form['option_list']:
                print(option)
                self.fields['choice_{}-{}'.format(option['type'], option['obj'].id)] = forms.ChoiceField(label=option['obj'].option_text, choices=choices, required=False)

        if self.form_type == 'checkbox':
            for option in dynamic_form['option_list']:
                print(option)
                self.fields['choice_{}-{}'.format(option['type'], option['obj'].id)] = forms.BooleanField(label=option['obj'].option_text, required=False)

        if self.form_type == 'radio':
            choices = []
            for option in dynamic_form['option_list']:
                #options types are 'normal' or 'write_in'
                choices.append(('{}-{}'.format(option['type'], option['obj'].id),option['obj'].option_text,))

            self.fields['choice'] = forms.ChoiceField( widget=forms.RadioSelect(), choices=choices, required=False)


    def dynamic_answers(self):
        for name, value in self.cleaned_data.items():
            if name.startswith('choice_'):
                yield (self.fields[name].label, value)

    def clean(self):
        cleaned_data = super(MultiVoteForm, self).clean()
        if self.form_type == "ranked":
            #make sure no duplicate ranks exist
            no_dups = {}

            for key, value in cleaned_data.items():
                if value:
                    if value not in no_dups:
                        no_dups[value] = [key]
                    else:
                        #duplicate value, raise error
                        no_dups[value].append(key)

            for value,key in no_dups.items():
                if len(key) > 1:
                    for k in key:
                        self.add_error(k,"Two options cannot have the same rank.")

        if  self.form_type == "checkbox":
            #make sure no more than max choices
            print("hiiiiiii")
            print(self.max_choices)

            count_selected = 0
            for item, value in cleaned_data.items():
                if value:
                    count_selected += 1
            print(count_selected)
            if self.max_choices:
                if count_selected > self.max_choices:
                    print("raising error")
                    raise forms.ValidationError(_("The maximum number of choices is {}.".format(self.max_choices)), code="MORE_THAN")
